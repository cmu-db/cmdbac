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
## Drupal DEPLOYER
## =====================================================================
class DrupalDeployer(BaseDeployer):
    def __init__(self, repo, database, deploy_id, database_config = None, runtime = None):
        BaseDeployer.__init__(self, repo, database, deploy_id, database_config, runtime)
        if database_config == None:
            self.database_config['name'] = 'drupal_app' + str(deploy_id)
        self.main_filename = None

        ## HACK
        self.database_config['password'] = ''
    ## DEF

    def configure_settings(self, path):
        pass
    ## DEF
    
    def get_main_url(self):
        return 'http://127.0.0.1:{}/'.format(self.port)
    ## DEF

    def sync_server(self, path):
        LOG.info('Syncing server ...')
        utils.run_command('{} && drush dl php_server'.format(
            utils.cd(path)))
        utils.run_command_async('drush ss', input=['0.0.0.0\n', '{}\n'.format(self.port)], cwd=path)

        time.sleep(5)



    ## DEF

    def run_server(self, path):
        pass
    ## DEF

    def get_runtime(self):
        out = utils.run_command('php -v')
        return {
            'executable': 'php',
            'version': out[1].split('\n')[0].split()[1]
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

        self.sync_server(deploy_path)

        return ATTEMPT_STATUS_SUCCESS

        self.run_server(deploy_path)
        time.sleep(5)
        
        attemptStatus = self.check_server()

        return attemptStatus
    ## DEF
    
    def deploy_repo_attempt(self, deploy_path):
        package_jsons = utils.search_file(deploy_path, 'install.php')
        base_dir = sorted([os.path.dirname(package_json) for package_json in package_jsons])[0]

        # TODO : delete robots.txt

        self.setting_path = base_dir

        print self.setting_path

        return self.try_deploy(base_dir)
    ## DEF
    
## CLASS