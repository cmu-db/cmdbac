import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import time
import json
import re

from url import URL
from utils import Utils
from string import Template
from bs4 import BeautifulSoup
from datetime import datetime

from crawler.models import *

class BaseDeployer(object):
    TMP_ZIP = "tmp.zip"
    TMP_DEPLOY_PATH = "tmp_dir"
    
    def __init__(self, repo):
        self.repo = repo
        self.installed_requirements = [ ]
        self.packages_from_file = [ ]
        self.packages_from_database = [ ]
        self.requirement_files = None
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
    
    def get_urls(self, path):
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
        LOG.info('deploying repo: ' + self.repo.name)
        
        attempt = Attempt()
        attempt.repo = repo
        attempt.result = ATTEMPT_STATUS_DEPLOYING
        attempt.start_time = datetime.datetime.now()
        attempt.hostname = socket.gethostname()
        attempt.save()

        self.repo.latest_attempt = attempt
        self.repo.attempts_count = repo.attempts_count + 1
        self.repo.save()
        try:
            sha = get_latest_sha(self.repo)
        except:
            self.save_attempt(ATTEMPT_STATUS_DOWNLOAD_ERROR)
            return
        attempt.sha = sha

        LOG.info('Downloading repo: ' + repo.name + attempt.sha)
        try:
            download(attempt, TMP_ZIP)
        except:
            print traceback.print_exc()
            save_attempt(attempt, ATTEMPT_STATUS_DOWNLOAD_ERROR)
            return
        remake_dir(TMP_DEPLOY_PATH)
        unzip(TMP_ZIP, TMP_DEPLOY_PATH)
        LOG.info('DIR = ' + TMP_DEPLOY_PATH)
        self.deployRepoAttempt(attempt, TMP_DEPLOY_PATH)
        
        # Check whether the web app is running
        urls = self.get_urls(os.path.dirname(setting_file))
        LOG.info("urls = " + urls)
        urls = list(set([re.sub(r'[\^\$]', '', url) for url in urls if '?' not in url]))
        urls = sorted(urls, key=len)
        attemptStatus = ATTEMPT_STATUS_SUCCESS
        for url in urls:
            out = self.check_server(url)
            LOG.info(out)
            if not "200 OK" in out:
                attemptStatus = ATTEMPT_STATUS_RUNNING_ERROR
        self.save_attempt(attempt, attemptStatus, out, installed_requirements, packages_from_database)
        self.kill_server()
        
    ## DEF
    
    def save_attempt(self, attempt, result, log_str):
        attempt.result = result
        attempt.log = log_str
        attempt.duration = datetime.datetime.now()
        attempt.save()
        
        # Populate packages
        for pkg in self.packages_from_file:
            dep = Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=PACKAGE_SOURCE_FILE))
            pkg.count = pkg.count + 1
            pkg.save()
        ## FOR
        for pkg in packages_from_database:
            Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=PACKAGE_SOURCE_DATABASE)
        ## FOR
    ## DEF
    
    

## CLASS