import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import time
import json
import re
import logging
import socket
import pkgutil
import traceback
import urllib2
import shutil

from StringIO import StringIO
from string import Template
from bs4 import BeautifulSoup
from datetime import datetime

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
    TMP_ZIP = "tmp.zip"
    TMP_DEPLOY_PATH = "/tmp/crawler"
    
    def __init__(self, repo, database):
        self.repo = repo
        self.database = database
        self.installed_requirements = [ ]
        self.packages_from_file = [ ]
        self.packages_from_database = [ ]
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
    
    def rewrite_settings(self, settings_file):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def install_requirements(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def deploy_repo_attempt(self, attempt, path):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def get_urls(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def check_server(self, url):
        LOG.info("Checking server...")
        url = urlparse.urljoin("http://localhost:%d/" % self.repo.project_type.default_port, url)
        command = "wget --spider " + url
        return utils.run_command(command)
    ## DEF
    
    def kill_server(self):
        LOG.info("Killing server on port %d..." % self.repo.project_type.default_port)
        command = "fuser -k %s/tcp" % self.repo.project_type.default_port
        return utils.run_command(command)
    ## DEF
        
    def run_server(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def sync_server(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
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
            print traceback.print_exc()
            self.save_attempt(attempt, ATTEMPT_STATUS_DOWNLOAD_ERROR)
            return

        LOG.info('Downloading at {} ...'.format(attempt.sha))
        try:
            utils.download_repo(attempt, BaseDeployer.TMP_ZIP)
        except:
            print traceback.print_exc()
            self.save_attempt(attempt, ATTEMPT_STATUS_DOWNLOAD_ERROR)
            return
        
        utils.remake_dir(BaseDeployer.TMP_DEPLOY_PATH)
        utils.unzip(BaseDeployer.TMP_ZIP, BaseDeployer.TMP_DEPLOY_PATH)
        LOG.info('Deploy at {} ...'.format(BaseDeployer.TMP_DEPLOY_PATH))
        
        try:
            attemptStatus = self.deploy_repo_attempt(attempt, BaseDeployer.TMP_DEPLOY_PATH)
        except:
            print traceback.print_exc()
            self.save_attempt(attempt, ATTEMPT_STATUS_RUNNING_ERROR)
            return
        if attemptStatus != ATTEMPT_STATUS_SUCCESS:
            self.save_attempt(attempt, attemptStatus)
        
        # Check whether the web app is running
        urls = self.get_urls()
        LOG.info("urls = " + str(urls))
        urls = list(set([re.sub(r'[\^\$]', '', url) for url in urls if '?' not in url]))
        urls = sorted(urls, key=len)
        for url in urls:
            out = self.check_server(url)
            LOG.info(out)
            if not "200 OK" in out:
                attemptStatus = ATTEMPT_STATUS_RUNNING_ERROR
        self.kill_server()
        
        # Okay we've seen everything that we wanted to see...
        self.save_attempt(attempt, attemptStatus)
        
        return
    ## DEF
    
    def save_attempt(self, attempt, result):
        # Stop the log capture
        self.log.removeHandler(self.logHandler)
        self.logHandler.flush()
        self.buffer.flush()
        
        attempt.result = result
        attempt.log = self.buffer.getvalue()
        attempt.stop_time = datetime.now()
        attempt.save()
        LOG.info("Saved Attempt #%s for %s" % (attempt, attempt.repo))
        
        # Populate packages
        for pkg in self.packages_from_file:
            dep = Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=PACKAGE_SOURCE_FILE)
            pkg.count = pkg.count + 1
            pkg.save()
        ## FOR
        for pkg in self.packages_from_database:
            Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=PACKAGE_SOURCE_DATABASE)
        ## FOR

        # Make sure we update the repo to point to this 
        # latest attempt
        self.repo.valid_project = (result == ATTEMPT_STATUS_SUCCESS)
        self.repo.latest_attempt = attempt
        self.repo.attempts_count = self.repo.attempts_count + 1
        self.repo.save()

    ## DEF
## CLASS
