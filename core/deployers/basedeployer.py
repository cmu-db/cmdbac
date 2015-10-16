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
from drivers import *
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
    
    def __init__(self, repo, database, deploy_id):
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
            cur.execute('drop database if exists {}'.format(self.database_name))
            cur.execute('create database {}'.format(self.database_name))
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

    def save_attempt(self, attempt, attempt_result, driver_result = {}):
        register_result = driver_result.get('register', USER_STATUS_UNKNOWN)
        login_result = driver_result.get('login', USER_STATUS_UNKNOWN)
        forms = driver_result.get('forms', None)
        screenshot_path = driver_result.get('screenshot', None)

        # stop capturing the log
        self.log.removeHandler(self.logHandler)
        self.logHandler.flush()
        self.buffer.flush()

        # get runtime
        if self.runtime == None:
            self.runtime = self.get_runtime()
        Runtime.objects.get_or_create(executable = self.runtime['executable'], version = self.runtime['version'])
        runtime = Runtime.objects.get(executable = self.runtime['executable'], version = self.runtime['version'])


        # save attempt
        attempt.result = attempt_result
        attempt.login = login_result
        attempt.register = register_result
        attempt.log = self.buffer.getvalue()
        attempt.stop_time = datetime.now()
        attempt.size = utils.get_size(self.base_path)
        attempt.runtime = runtime
        attempt.save()

        # save forms
        if forms != None:
            for f in forms:
                form = Form()
                form.action = f['action']
                form.url = f['url']
                form.attempt = attempt
                form.save()
                for q in f['queries']:
                    query = Query()
                    query.content = q
                    query.form = form
                    query.save()
                for input in f['inputs']:
                    field = Field()
                    field.name = input['name']
                    field.type = input['type']
                    field.form = form
                    field.save()

        # save screenshot
        if screenshot_path != None:
            screenshot = open(screenshot_path, 'rb')
            image = Image()
            image.data = screenshot.read()
            image.attempt = attempt
            image.save()

        LOG.info("Saved Attempt #%s for %s" % (attempt, attempt.repo))
        
        # populate packages
        for pkg in self.packages_from_file:
            Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=PACKAGE_SOURCE_FILE)
            pkg.count = pkg.count + 1
            pkg.save()  
        ## FOR
        for pkg in self.packages_from_database:
            Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=PACKAGE_SOURCE_DATABASE)
            if pkg.version != '':
                pkg.count = pkg.count + 1
                pkg.save()
        ## FOR

        # make sure we update the repo to point to this latest attempt
        if attempt_result in [ATTEMPT_STATUS_MISSING_REQUIRED_FILES]:
            self.repo.valid_project = False
        else:
            self.repo.valid_project = True
        self.repo.latest_attempt = attempt
        self.repo.save()
    ## DEF
    
    def deploy(self):
        LOG.info('Deploying repo: {} ...'.format(self.repo.name))
        
        attempt = Attempt()
        attempt.repo = self.repo
        attempt.database = self.database
        attempt.result = ATTEMPT_STATUS_DEPLOYING
        attempt.start_time = datetime.now()
        attempt.hostname = socket.gethostname()
        LOG.info('Validating ...')
        try:
            attempt.sha = utils.get_latest_sha(self.repo)
        except Exception, e:
            LOG.exception(e)
            self.save_attempt(attempt, ATTEMPT_STATUS_DOWNLOAD_ERROR)
            return -1

        LOG.info('Downloading at {} ...'.format(attempt.sha))
        try:
            utils.download_repo(attempt, self.zip_file)
        except Exception, e:
            LOG.exception(e)
            self.save_attempt(attempt, ATTEMPT_STATUS_DOWNLOAD_ERROR)
            return -1
        
        try:
            utils.make_dir(self.base_path)
            utils.unzip(self.zip_file, self.base_path)
        except Exception, e:
            LOG.exception(e)
            self.save_attempt(attempt, ATTEMPT_STATUS_DOWNLOAD_ERROR)
            return -1

        LOG.info('Deploying at {} ...'.format(self.base_path))
        
        try:
            attemptStatus = self.deploy_repo_attempt(attempt, self.base_path)
        except Exception, e:
            LOG.exception(e)
            self.save_attempt(attempt, ATTEMPT_STATUS_RUNNING_ERROR)
            return -1
           
        if attemptStatus != ATTEMPT_STATUS_SUCCESS:
            self.save_attempt(attempt, attemptStatus)
            return -1

        try:
            driver = Driver()
            driverResult = driver.drive(self)
        except Exception, e:
            LOG.exception(e)
            driverResult = {}

        self.kill_server()

        self.save_attempt(attempt, attemptStatus, driverResult)
        
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
