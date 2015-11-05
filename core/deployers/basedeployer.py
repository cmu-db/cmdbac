import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import socket
import urlparse
from StringIO import StringIO
from string import Template
from datetime import datetime
import MySQLdb

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
from crawler.models import *
import utils

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()
LOG_handler = logging.StreamHandler()
LOG_formatter = logging.Formatter(fmt='%(asctime)s [%(filename)s:%(funcName)s:%(lineno)03d] %(levelname)-5s: %(message)s',
                                  datefmt='%m-%d-%Y %H:%M:%S')
LOG_handler.setFormatter(LOG_formatter)
LOG.addHandler(LOG_handler)
LOG.setLevel(logging.INFO)

## =====================================================================
## BASE DEPLOYER
## =====================================================================
class BaseDeployer(object):
    TMP_ZIP_FILE = "tmp.zip"
    TMP_DEPLOY_PATH = "/tmp/crawler"
    
    def __init__(self, repo, database, deploy_id, database_config = None):
        self.repo = repo
        self.database = database
        self.requirement_files = None
        self.packages_from_database = []
        self.packages_from_file = []
        self.deploy_id = deploy_id
        self.zip_file = self.TMP_ZIP_FILE + str(self.deploy_id)
        self.base_path = self.TMP_DEPLOY_PATH + str(self.deploy_id)
        self.setting_path = None
        self.port = int(self.repo.project_type.default_port) + int(self.deploy_id)
        self.runtime = None

        if database_config == None:
            self.database_config = {
                'host': '127.0.0.1',
                'port': '3306',
                'username': 'root',
                'password': 'root'
            }
        else:
            self.database_config = database_config

        # Create a buffer so that we can capture all log commands to include in the database for this attempt
        self.log = logging.getLogger()
        self.buffer = StringIO()
        self.logHandler = logging.StreamHandler(self.buffer)
        self.logHandler.setFormatter(LOG_formatter)
        self.log.addHandler(self.logHandler)    
    ## DEF
    
    def get_database(self, settings_file):
        db = Database.objects.get(name__iexact="MySQL")
        return db
    ## DEF
    
    def clear_database(self):
        try:
            conn = MySQLdb.connect(host='localhost',user='root',passwd='root',port=3306)
            cur = conn.cursor()
            cur.execute('drop database if exists {}'.format(self.database_config['name']))
            cur.execute('create database {}'.format(self.database_config['name']))
            conn.commit()
            cur.close()
            conn.close()
        except Exception, e:
            LOG.exception(e)
    ## DEF
    
    def extract_database_info(self):
        try:
            conn = MySQLdb.connect(host='localhost',user='root',passwd='root',db=self.database_name, port=3306)
            cur = conn.cursor()
            cur.close()
            conn.close()
        except Exception, e:
            LOG.exception(e)
    ## DEF

    def get_main_url(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF

    def configure_network(self):
        LOG.info('Configuring network ...')
        utils.block_network()
    ## DEF

    def run_server(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF

    def deploy_repo_attempt(self, attempt, path):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF

    def get_runtime(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF

    def flush_log(self):
        # stop capturing the log
        self.log.removeHandler(self.logHandler)
        self.logHandler.flush()
        self.buffer.flush()
        self.attempt.log = self.buffer.getvalue()


    def save_attempt(self, attempt_result, driver_result = {}):
        # flush log
        self.flush_log()

        # get info
        register_result = driver_result.get('register', USER_STATUS_UNKNOWN)
        login_result = driver_result.get('login', USER_STATUS_UNKNOWN)
        forms = driver_result.get('forms', None)
        screenshot_path = driver_result.get('screenshot', None)

        # get runtime
        if self.runtime == None:
            self.runtime = self.get_runtime()
        Runtime.objects.get_or_create(executable = self.runtime['executable'], version = self.runtime['version'])
        runtime = Runtime.objects.get(executable = self.runtime['executable'], version = self.runtime['version'])


        # save attempt
        self.attempt.result = attempt_result
        self.attempt.login = login_result
        self.attempt.register = register_result
        self.attempt.stop_time = datetime.now()
        self.attempt.size = utils.get_size(self.base_path)
        self.attempt.runtime = runtime
        if forms != None:
            self.attempt.forms_count = len(forms)
            self.attempt.queries_count = sum(len(form['queries']) for form in forms)
        self.attempt.save()

        # save forms
        if forms != None:
            for f in forms:
                form = Form()
                form.action = f['action']
                form.url = f['url']
                form.attempt = self.attempt
                if 'admin' in f:
                    form.admin = True
                form.save()
                for q in f['queries']:
                    query = Query()
                    query.content = q['content']
                    query.matched = q['matched']
                    query.form = form
                    query.save()
                for input in f['inputs']:
                    field = Field()
                    field.name = input['name']
                    field.type = input['type']
                    field.form = form
                    field.save()
                for description, count in f['counter'].iteritems():
                    counter = Counter()
                    counter.description = description
                    counter.count = count
                    counter.form = form
                    counter.save()

        # save screenshot
        if screenshot_path != None:
            screenshot = open(screenshot_path, 'rb')
            image = Image()
            image.data = screenshot.read()
            image.attempt = self.attempt
            image.save()

        LOG.info("Saved Attempt #%s for %s" % (self.attempt, self.attempt.repo))
        
        # populate packages
        for pkg in self.packages_from_file:
            try:
                Dependency.objects.get_or_create(attempt=self.attempt, package=pkg, source=PACKAGE_SOURCE_FILE)
                pkg.count = pkg.count + 1
                pkg.save()
            except Exception, e:
                LOG.exception(e)  
        ## FOR
        for pkg in self.packages_from_database:
            try:
                Dependency.objects.get_or_create(attempt=self.attempt, package=pkg, source=PACKAGE_SOURCE_DATABASE)
                if pkg.version != '':
                    pkg.count = pkg.count + 1
                    pkg.save()
            except Exception, e:
                LOG.exception(e)
        ## FOR

        # make sure we update the repo to point to this latest attempt
        if attempt_result in [ATTEMPT_STATUS_MISSING_REQUIRED_FILES]:
            self.repo.valid_project = False
        else:
            self.repo.valid_project = True
        self.repo.latest_attempt = self.attempt
        self.repo.attempts_count = self.repo.attempts_count + 1
        self.repo.save()
    ## DEF
    
    def deploy(self, save = True):
        LOG.info('Deploying repo: {} ...'.format(self.repo.name))
        
        self.attempt = Attempt()
        self.attempt.repo = self.repo
        self.attempt.database = self.database
        self.attempt.result = ATTEMPT_STATUS_DEPLOYING
        self.attempt.start_time = datetime.now()
        self.attempt.hostname = socket.gethostname()
        LOG.info('Validating ...')
        try:
            self.attempt.sha = utils.get_latest_sha(self.repo)
        except Exception, e:
            LOG.exception(e)
            if save:
                self.save_attempt(ATTEMPT_STATUS_DOWNLOAD_ERROR)
            else:
                LOG.error('Download Error..')
            return -1

        LOG.info('Downloading at {} ...'.format(self.attempt.sha))
        try:
            utils.download_repo(self.attempt, self.zip_file)
        except Exception, e:
            LOG.exception(e)
            if save:
                self.save_attempt(ATTEMPT_STATUS_DOWNLOAD_ERROR)
            else:
                LOG.error('Download Error..')
            return -1
        
        try:
            utils.make_dir(self.base_path)
            utils.unzip(self.zip_file, self.base_path)
        except Exception, e:
            LOG.exception(e)
            if save:
                self.save_attempt(ATTEMPT_STATUS_DOWNLOAD_ERROR)
            else:
                LOG.error('Download Error..')
            return -1

        LOG.info('Deploying at {} ...'.format(self.base_path))
        
        try:
            attemptStatus = self.deploy_repo_attempt(self.base_path)
        except Exception, e:
            LOG.exception(e)
            if save:
                self.save_attempt(ATTEMPT_STATUS_RUNNING_ERROR)
            else:
                LOG.error('Running Error...')
            return -1
           
        if attemptStatus != ATTEMPT_STATUS_SUCCESS:
            if save:
                self.save_attempt(attemptStatus)
            return -1
        
        return 0
    ## DEF

    def check_server(self):
        LOG.info("Checking server ...")
        url = self.get_main_url()
        command = 'wget --spider {}'.format(url)
        out = utils.run_command(command)
        LOG.info(out)
        if not "200 OK" in out[2]:
            return ATTEMPT_STATUS_RUNNING_ERROR
        else:
            return ATTEMPT_STATUS_SUCCESS
    ## DEF

    def kill_server(self):
        LOG.info('Killing server on port {} ...'.format(self.port))
        ret = utils.kill_port(self.port)
        utils.unblock_network()
        return ret
    ## DEF
    
## CLASS
