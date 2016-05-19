import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import re
import time

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


## =====================================================================
## GRAILS DEPLOYER
## =====================================================================
class GrailsDeployer(BaseDeployer):
    def __init__(self, repo, database, deploy_id, database_config = None):
        BaseDeployer.__init__(self, repo, database, deploy_id, database_config)
        if database_config == None:
            self.database_config['name'] = 'grails_app' + str(deploy_id)
        self.main_filename = None
    ## DEF
    
    def configure_settings(self, path):
        pass
    ## DEF
    
    def install_requirements(self, path):
        if path:
            command = '{} && export JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64 && ./grailsw compile'.format(utils.cd(path))
            out = utils.run_command(command)
            if out[1] == '':
                return out[2]
            else:
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
        command = '{} && export JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64 && ./grailsw run-app'.format(
            utils.cd(path))
        return utils.run_command_async(command)
    ## DEF

    def get_runtime(self):
        out = utils.run_command('node -v')
        return {
            'executable': 'node',
            'version': out[1][1:]
        }
    ## DEF

    def try_deploy(self, deploy_path):
        LOG.info('Configuring settings ...')
        self.kill_server()
        self.clear_database()
        self.configure_settings(deploy_path)
        self.runtime = self.get_runtime()
        LOG.info(self.runtime)

        self.attempt.database = self.get_database()
        LOG.info('Database: ' + self.attempt.database.name)

        LOG.info('Installing requirements ...')
        out = self.install_requirements(deploy_path)
        LOG.info(out)

        self.run_server(deploy_path)
        
        retry_times = 0
        while retry_times < 5:
            time.sleep(30)
            attemptStatus = self.check_server()
            if attemptStatus == ATTEMPT_STATUS_SUCCESS:
                break
            retry_times += 1

        return attemptStatus
    ## DEF
    
    def deploy_repo_attempt(self, deploy_path):
        grailsw_files = utils.search_file(deploy_path, 'grailsw')
        if not grailsw_files:
            LOG.error('No grailsw found!')
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        base_dir = sorted([os.path.dirname(grailsw_file) for grailsw_file in grailsw_files])[0]

        self.setting_path = base_dir

        return self.try_deploy(base_dir)
    ## DEF
    
## CLASS