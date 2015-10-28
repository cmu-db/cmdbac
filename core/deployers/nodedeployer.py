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
    ## DEF
    
    def install_requirements(self, path):
    ## DEF
    
    def get_main_url(self):
        return 'http://127.0.0.1:{}/'.format(self.port)
    ## DEF

    def sync_server(self, path):
    ## DEF

    def run_server(self, path):
    ## DEF

    def get_runtime(self):
    ## DEF

    def try_deploy(self, deploy_path):
        LOG.info('Configuring settings ...')
        self.kill_server()
        self.clear_database()
        self.configure_settings()
        self.runtime = self.get_runtime()

        self.attempt.database = self.get_database('')
        LOG.info('Database: ' + self.attempt.database.name)

        # TODO: deploy the repo
        LOG.info(self.run_server(deploy_path))

        attemptStatus = self.check_server()

        return attemptStatus
    ## DEF
    
    def deploy_repo_attempt(self, deploy_path):
        pass
    ## DEF
    
## CLASS