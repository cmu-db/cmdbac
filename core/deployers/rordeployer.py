import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import re

from basedeployer import BaseDeployer
from library.models import *
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
  adapter: {adapter}
  database: {name}
  pool: 5
  timeout: 5000
  username: {username}
  password: {password}
  port: {port}
  host: {host}
test:
  adapter: {adapter}
  database: {name}
  pool: 5
  timeout: 5000
  username: {username}
  password: {password}
  port: {port}
  host: {host}
production:
  adapter: {adapter}
  database: {name}
  pool: 5
  timeout: 5000
  username: {username}
  password: {password}
  port: {port}
  host: {host}
"""

GEMFILE_SETTINGS = """
gem '{}'
"""

## =====================================================================
## RUBY ON RAILS DEPLOYER
## =====================================================================
class RoRDeployer(BaseDeployer):
    def __init__(self, repo, database, deploy_id, database_config = None):
        BaseDeployer.__init__(self, repo, database, deploy_id, database_config)
        if database_config == None:
            self.database_config['name'] = 'ror_app' + str(deploy_id)
    ## DEF
    
    def configure_settings(self):
        adapter = {
            'MySQL': 'mysql2',
            'PostgreSQL': 'postgresql',
            'SQLite3': 'sqlite3'
        }[self.database.name]
        with open(os.path.join(self.setting_path, 'config/database.yml'), "w") as my_file:
            my_file.write(DATABASE_SETTINGS.format(name=self.database_config['name'], 
                username=self.database_config['username'], password=self.database_config['password'],
                port=self.database_config['port'], host=self.database_config['host'], adapter=adapter))
        ## WITH
        with open(os.path.join(self.setting_path, 'Gemfile'), "a") as my_file:
            my_file.write(GEMFILE_SETTINGS.format(adapter))
        ## WITH
    ## DEF
    
    def install_requirements(self, path):
        if path:
            command = '{} && {} && bundle install'.format(
                  utils.cd(path),
                  utils.use_ruby_version(self.runtime['version']))
            out = utils.run_command(command)
            return out[1]
        return ''
    ## DEF
    
    def get_main_url(self):
        return 'http://127.0.0.1:{}/'.format(self.port)
    ## DEF

    def sync_server(self, path):
        LOG.info('Syncing server ...')
        command = '{} && {} && bundle exec rake db:migrate'.format(
            utils.cd(path),
            utils.use_ruby_version(self.runtime['version']))
        return utils.run_command(command)
    ## DEF

    def run_server(self, path, port):
        self.configure_network()
        LOG.info('Running server ...')
        command = '{} && {} && bundle exec rails server -p {} -d'.format(
            utils.cd(path), 
            utils.use_ruby_version(self.runtime['version']),
            port)
        return utils.run_command(command)
    ## DEF

    def get_runtime(self, version = None):
    	latest_successful_attempt = self.get_latest_successful_attempt()
        if latest_successful_attempt != None:
            return {
                'executable': latest_successful_attempt.runtime.executable,
                'version': latest_successful_attempt.runtime.version
            }
        else:
            if version != None:
                return {
                    'executable': 'ruby',
                    'version': version
                }
            else:
                out = utils.run_command('ruby -v')[1].split(' ')
                return {
                    'executable': 'ruby',
                    'version': out[1]
                }
    ## DEF

    def try_deploy(self, deploy_path):
        LOG.info('Configuring settings ...')
        self.kill_server()
        self.clear_database()
        self.configure_settings()

        # get runtime
        ruby_versions = utils.get_ruby_versions()
        ruby_version = ruby_versions[2]
        self.runtime = self.get_runtime(ruby_version)
        LOG.info(self.runtime)
        
        self.attempt.database = self.get_database()
        LOG.info('Database: ' + self.attempt.database.name)

        LOG.info('Using Ruby {} ...'.format(ruby_version))
    
        LOG.info('Installing requirements ...')
        out = self.install_requirements(deploy_path)
        if not 'complete!' in out:
            LOG.info(out)
            return ATTEMPT_STATUS_MISSING_DEPENDENCIES
        packages = out.split('\n')
        for package in packages:
            s = re.search('Using (.*) (.*)', package)
            if s:
                name, version = s.group(1), s.group(2)
                try:
                    pkg, created = Package.objects.get_or_create(name=name, version=version, project_type=self.repo.project_type)
                    self.packages_from_file.append(pkg)
                except Exception, e:
                    LOG.exception(e)

        out = self.sync_server(deploy_path)
        if 'rake aborted!' in out[1]:
            LOG.info(out)
            return ATTEMPT_STATUS_DATABASE_ERROR
        
        self.run_server(deploy_path, self.port)

        attemptStatus = self.check_server()

        return attemptStatus
    ## DEF
    
    def deploy_repo_attempt(self, deploy_path):
        rakefiles = utils.search_file(deploy_path, 'Rakefile')
        if not rakefiles:
            LOG.error('No rakefile found!')
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        rakefile_paths = [os.path.dirname(rakefile) for rakefile in rakefiles]
        

        gemfiles = utils.search_file(deploy_path, 'Gemfile')
        if not gemfiles:
            LOG.error('No gemfile found!')
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        gemfile_paths = [os.path.dirname(gemfile) for gemfile in gemfiles]

        base_dirs = set.intersection(set(rakefile_paths), set(gemfile_paths))
        if not base_dirs:
            LOG.error('Can not find base directory!')
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        base_dir = next(iter(base_dirs))

        self.setting_path = base_dir

        return self.try_deploy(base_dir)
    ## DEF
    
## CLASS
