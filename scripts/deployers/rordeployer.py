import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
import re

from basedeployer import BaseDeployer
from crawler.models import *
import utils

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## =====================================================================
## SETTINGS
## =====================================================================
DATABASE_SETTINGS = """
development:
  adapter: sqlite3
  database: db/development.sqlite3
  pool: 5
  timeout: 5000

test:
  adapter: sqlite3
  database: db/test.sqlite3
  pool: 5
  timeout: 5000

production:
  adapter: sqlite3
  database: db/production.sqlite3
  pool: 5
  timeout: 5000
"""

GEMFILE_SETTINGS = """
gem 'sqlite3'
"""


## =====================================================================
## RUBY ON RAILS DEPLOYER
## =====================================================================
class RoRDeployer(BaseDeployer):
    def __init__(self, repo, database):
        BaseDeployer.__init__(self, repo, database)
        self.setting_file = None
    ## DEF
    
    def getDatabase(self, settings_file):
        pass
    ## DEF
    
    def rewrite_settings(self, path):
        with open(os.path.join(path, 'config/database.yml'), "w") as my_file:
            my_file.write(DATABASE_SETTINGS)
        ## WITH
        with open(os.path.join(path, 'Gemfile'), "a") as my_file:
            my_file.write(GEMFILE_SETTINGS)
        ## WITH
    ## DEF
    
    def install_requirements(self, requirement_files):
        if requirement_files:
            command = vagrant_cd(requirement_files) + " && bundle install"
            return vagrant_run_command(command)
        return []
    ## DEF
    
    def get_urls(self):
        setting_files = utils.search_file(BaseDeployer.TMP_DEPLOY_PATH, 'settings.py')[0]
        dirname = os.path.dirname(setting_files)
        sys.path.append(dirname)
        proj_name = os.path.basename(setting_files)
        command = "python " + utils.to_vm_path('get_urls.py') + ' ' + utils.to_vm_path(dirname) + ' ' + proj_name
        out = utils.vagrant_run_command(command).strip()
        if not out:
            urls = []
        else:
            urls = out.splitlines()
        return urls
    ## DEF
    
    def deployRepoAttempt(self, attempt, deployPath):
        pass
    ## DEF
    
    def tryDeploy(self, attempt, manage_file, setting_file):
        pass
        
    ## DEF
    
    def checkServer(self, url):
        LOG.info("Checking server...")
        command = "wget --spider " + urlparse.urljoin("http://localhost:3000/", url)
        return utils.vagrant_run_command(command)
    ## DEF
    
    def killServer(self):
        LOG.info("Killing server...")
        command = "fuser -k 3000/tcp"
        return utils.vagrant_run_command(command)
    ## DEF
    
    def runServer(self, path):
        LOG.info("Run server...")
        #command = vagrant_cd(path) + " && bundle exec rails server -p 3000 > /vagrant/log 2>&1 & sleep 10"
        command = vagrant_cd(path) + " && nohup bundle exec rails server -p 3000 -d"
        return vagrant_run_command(command)
    ## DEF
    
    def syncServer(self, path):
        LOG.info("Sync server...")
        command = vagrant_cd(path) + " && bundle exec rake db:migrate"
        return utils.vagrant_run_command(command)
    ## DEF
    
## CLASS