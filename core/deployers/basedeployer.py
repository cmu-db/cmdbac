import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import socket
import traceback
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
    TMP_ZIP = "tmp.zip"
    TMP_DEPLOY_PATH = "/tmp/crawler"
    
    def __init__(self, repo, database):
        self.repo = repo
        self.database = database
        self.requirement_files = None
        
        # Create a buffer so that we can capture all log commands 
        # to include in the database for this attempt
        self.log = logging.getLogger()
        self.buffer = StringIO()
        self.logHandler = logging.StreamHandler(self.buffer)
        formatter = logging.Formatter("%(message)s")
        self.logHandler.setFormatter(formatter)
        self.log.addHandler(self.logHandler)    
    ## DEF
    
    def get_database(self, settings_file):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
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
        except:
            # print traceback.print_exc()
            pass
    ## DEF

    def extract_database_info(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF

    def configure_settings(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def install_requirements(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF

    def get_urls(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF

    def get_main_url(self):
        urls = self.get_urls()
        for url in urls:
            if not url.startswith('admin/'):
                ret_url = 'http://127.0.0.1:{}/'.format(self.repo.project_type.default_port)
                ret_url = urlparse.urljoin(ret_url, url)
                return ret_url
        return None
    ## DEF

    def sync_server(self):
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

    def save_attempt(self, attempt, result, register_result = USER_STATUS_UNKNOWN, login_result = USER_STATUS_UNKNOWN, forms = None):
        # Stop the log capture
        self.log.removeHandler(self.logHandler)
        self.logHandler.flush()
        self.buffer.flush()
        
        attempt.result = result
        attempt.login = login_result
        attempt.register = register_result
        attempt.log = self.buffer.getvalue()
        attempt.stop_time = datetime.now()
        attempt.save()
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

        LOG.info("Saved Attempt #%s for %s" % (attempt, attempt.repo))
        
        if 0:
            # Populate packages
            for pkg in self.packages_from_file:
                dep = Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=PACKAGE_SOURCE_FILE)
                pkg.count = pkg.count + 1
                pkg.save()
            ## FOR
            for pkg in self.packages_from_database:
                print pkg
                Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=PACKAGE_SOURCE_DATABASE)
            ## FOR

        # Make sure we update the repo to point to this 
        # latest attempt
        if self.repo.valid_project != ATTEMPT_STATUS_SUCCESS:
            self.repo.valid_project = (result == ATTEMPT_STATUS_SUCCESS)
        self.repo.latest_attempt = attempt
        self.repo.attempts_count = self.repo.attempts_count + 1
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
        except:
            # print traceback.print_exc()
            self.save_attempt(attempt, ATTEMPT_STATUS_DOWNLOAD_ERROR)
            return -1

        LOG.info('Downloading at {} ...'.format(attempt.sha))
        try:
            utils.download_repo(attempt, BaseDeployer.TMP_ZIP)
        except:
            # print traceback.print_exc()
            self.save_attempt(attempt, ATTEMPT_STATUS_DOWNLOAD_ERROR)
            return -1
        
        try:
            utils.remake_dir(BaseDeployer.TMP_DEPLOY_PATH)
            utils.unzip(BaseDeployer.TMP_ZIP, BaseDeployer.TMP_DEPLOY_PATH)
        except:
            # print traceback.print_exc()
            self.save_attempt(attempt, ATTEMPT_STATUS_DOWNLOAD_ERROR)
            return -1

        LOG.info('Deploying at {} ...'.format(BaseDeployer.TMP_DEPLOY_PATH))
        
        try:
            attemptStatus = self.deploy_repo_attempt(attempt, BaseDeployer.TMP_DEPLOY_PATH)
        except:
            print traceback.print_exc()
            # self.save_attempt(attempt, ATTEMPT_STATUS_RUNNING_ERROR)
            return -1
        if attemptStatus != ATTEMPT_STATUS_SUCCESS:
            self.save_attempt(attempt, attemptStatus)
            return -1
        
        # self.kill_server()

        driver = Driver()
        driverResult = driver.drive(self)

        self.save_attempt(attempt, attemptStatus, driverResult['register'], driverResult['login'], driverResult['forms'])
        
        raw_input('press any key to continue ...')

        return 0
    ## DEF

    def check_server(self, urls):
        LOG.info("Checking server ...")
        url = 'http://127.0.0.1:{}/'.format(self.repo.project_type.default_port)
        url = urlparse.urljoin(url, urls[0])
        command = 'wget --spider {}'.format(url)
        out = utils.run_command(command)
        LOG.info(out)
        if not "200 OK" in out[2]:
            return ATTEMPT_STATUS_RUNNING_ERROR
        else:
            return ATTEMPT_STATUS_SUCCESS
    ## DEF

    def kill_server(self):
        LOG.info('Killing server on port {} ...'.format(self.repo.project_type.default_port))
        ret = utils.kill_port(self.repo.project_type.default_port)
        utils.unblock_network()
        return ret
    ## DEF
    
## CLASS
