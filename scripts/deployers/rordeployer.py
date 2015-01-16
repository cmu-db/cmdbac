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
    
    def install_requirements(self):
        if self.requirement_files:
            command = vagrant_cd(self.requirement_files) + " && bundle install"
            out = vagrant_run_command(command)
            LOG.info(out)
            return out # ???
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
        rakefiles = utils.search_file(deployPath, 'Rakefile')
        if not rakefiles:
            LOG.error('no rakefile found')
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        rakefile_paths = [os.path.dirname(rakefile) for rakefile in rakefiles]
        #print 'rakefile_paths: ' + str(rakefile_paths)
        #elif len(rakefiles) != 1:
        #    print 'multiple rakefiles found'
        #    save_attempt(attempt, "Duplicate Required Files", log_str)
        #    continue
        
        # Finding database
        gemfiles = self.search_file(deployPath, 'Gemfile')
        if not gemfiles:
            LOG.error("No gemfile was found")
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        gemfile_paths = [os.path.dirname(gemfile) for gemfile in gemfiles]
        #print 'gemfile_paths: ' + str(gemfile_paths)
        db_files = search_file(DIR, 'database.yml')
        if not db_files:
            LOG.error("Unable to discover target database")
            self.save_attempt(attempt, ATTEMPT_STATUS_MISSING_REQUIRED_FILES)
            return

        LOG.info('using database')
        db_file_paths = [os.path.dirname(os.path.dirname(db_file)) for db_file in db_files if os.path.basename(os.path.normpath(os.path.dirname(db_file))) == "config"]
        #print 'db_file_paths: ' + str(db_file_paths)
        base_dirs = set.intersection(set(rakefile_paths), set(gemfile_paths), set(db_file_paths))
        if not base_dirs:
            LOG.error('can not find base directory')
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        base_dir = next(iter(base_dirs))
        attempt.base_dir = base_dir.split('/', 1)[1]
        LOG.info('base_dir: ' + base_dir)

        attempt.database = self.get_database(os.path.join(base_dir, 'config/database.yml'))
        LOG.info('database: ' + attempt.database.name)
        return self.tryDeploy(attempt, base_dir)
    ## DEF
    
    def tryDeploy(self, attempt, path):
        self.rewrite_settings(path)
        LOG.info('try deploy ror')
        self.killServer()
        
        out = self.install_requirements(path)
        LOG.info(out)
        if not "Your bundle is complete!" in out:
            return ATTEMPT_STATUS_MISSING_DEPENDENCIES

        out = self.syncServer(path)
        LOG.out(out)
        if "rake aborted!" in out:
            return ATTEMPT_STATUS_RUNNING_ERROR
        
        out = self.runServer(path)
        LOG.info(out)
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