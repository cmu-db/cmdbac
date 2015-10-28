import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import MySQLdb
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


## =====================================================================
## NODE.JS DEPLOYER
## =====================================================================
class NodeDeployer(BaseDeployer):
    def __init__(self, repo, database, deploy_id, database_config = None):
        BaseDeployer.__init__(self, repo, database, deploy_id, database_config)
        if database_config == None:
            self.database_config['name'] = 'node_app' + str(deploy_id)
    ## DEF
    
    def configure_settings(self):
        pass
    ## DEF
    
    def install_requirements(self, path):
        if path:
            command = '{} && npm install'.format(utils.cd(path))
            out = utils.run_command(command)
            return out[1]
        return ''
    ## DEF
    
    def get_main_url(self):
        return 'http://127.0.0.1:{}/'.format(self.port)
    ## DEF

    def sync_server(self, path):
        pass
    ## DEF

    def run_server(self, path):
        self.configure_network()
        LOG.info('Running server ...')
        command = '{} && node main'.format(
            utils.cd(path))
        return utils.run_command(command)
    ## DEF

    def get_runtime(self):
        out = utils.run_command('ruby -v')
        print out
        return {
            'executable': 'node',
            'version': '1'
        }
    ## DEF

    def try_deploy(self, deploy_path):
        LOG.info('Configuring settings ...')
        self.kill_server()
        self.clear_database()
        self.configure_settings()
        self.runtime = self.get_runtime()

        self.attempt.database = self.get_database('')
        LOG.info('Database: ' + self.attempt.database.name)

        LOG.info('Installing requirements ...')
        out = self.install_requirements(deploy_path)
        packages = out.split('\n')
        for package in packages:
            s = re.search('├── (.*)@(.*)', package)
            if s:
                name, version = s.group(1), s.group(2)
                print name, version
                continue
                try:
                    pkg, created = Package.objects.get_or_create(name=name, version=version, project_type=self.repo.project_type)
                    self.packages_from_file.append(pkg)
                except Exception, e:
                    LOG.exception(e)

        LOG.info(self.run_server(deploy_path))

        attemptStatus = self.check_server()

        return attemptStatus
    ## DEF
    
    def deploy_repo_attempt(self, deploy_path):
        package_jsons = utils.search_file(deploy_path, 'package.json')
        if not package_jsons:
            LOG.error('No package.json found!')
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        base_dir = next([os.path.dirname(package_json) for package_json in package_jsons])

        self.setting_path = base_dir

        return self.try_deploy(base_dir)
    ## DEF
    
## CLASS