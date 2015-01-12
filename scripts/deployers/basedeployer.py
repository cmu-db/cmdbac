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
LOG_formatter = logging.Formatter(fmt='%(asctime)s [%(funcName)s:%(lineno)03d] %(levelname)-5s: %(message)s',
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
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.logHandler.setFormatter(formatter)
        self.log.addHandler(self.logHandler)    
    ## DEF
    
    def getDatabase(self, settings_file):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def rewrite_settings(self, settings_file):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def install_requirements(self, requirement_files):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def deployRepoAttempt(self, attempt, path):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def get_urls(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def checkServer(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def killServer(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def runServer(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def syncServer(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF
    
    def deploy(self):
        self.log.info('Deploying repo: ' + self.repo.name)
        
        attempt = Attempt()
        attempt.repo = self.repo
        attempt.database = self.database
        attempt.result = ATTEMPT_STATUS_DEPLOYING
        attempt.start_time = datetime.now()
        attempt.hostname = socket.gethostname()
        try:
            attempt.sha = utils.get_latest_sha(self.repo)
        except:
            self.save_attempt(attempt, ATTEMPT_STATUS_DOWNLOAD_ERROR)
            return

        self.log.info('Downloading repo: ' + self.repo.name + attempt.sha)
        try:
            utils.download(attempt, BaseDeployer.TMP_ZIP)
        except:
            print traceback.print_exc()
            self.save_attempt(attempt, ATTEMPT_STATUS_DOWNLOAD_ERROR)
            return
        
        utils.remake_dir(BaseDeployer.TMP_DEPLOY_PATH)
        utils.unzip(BaseDeployer.TMP_ZIP, BaseDeployer.TMP_DEPLOY_PATH)
        self.log.info('DIR = ' + BaseDeployer.TMP_DEPLOY_PATH)
        
        try:
            self.deployRepoAttempt(attempt, BaseDeployer.TMP_DEPLOY_PATH)
        except:
            print traceback.print_exc()
            self.save_attempt(attempt, ATTEMPT_STATUS_RUNNING_ERROR)
            return
        
        # Check whether the web app is running
        urls = self.get_urls()
        self.log.info("urls = " + str(urls))
        urls = list(set([re.sub(r'[\^\$]', '', url) for url in urls if '?' not in url]))
        urls = sorted(urls, key=len)
        attemptStatus = ATTEMPT_STATUS_SUCCESS
        for url in urls:
            out = self.check_server(url)
            self.log.info(out)
            if not "200 OK" in out:
                attemptStatus = ATTEMPT_STATUS_RUNNING_ERROR
        self.save_attempt(attempt, attemptStatus)
        self.killServer()
        
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
        self.log.info("Saved Attempt #%s for %s" % (attempt, attempt.repo))
        
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
        self.repo.latest_attempt = attempt
        self.repo.attempts_count = self.repo.attempts_count + 1
        self.repo.save()

    ## DEF
## CLASS