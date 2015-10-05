import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import re
import time
import importlib
import traceback
import MySQLdb

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
## NODE DEPLOYER
## =====================================================================
class NodeDeployer(BaseDeployer):
    def __init__(self, repo, database):
        BaseDeployer.__init__(self, repo, database)
        self.database_name = 'node_app'
        self.setting_path = None
        self.requirement_files = None
    ## DEF
    
    def get_database(self, setting_file):
        db = Database.objects.get(name__iexact="MySQL")
        return db
    ## DEF

    def extract_database_info(self):
        try:
            conn = MySQLdb.connect(host='localhost',user='root',passwd='root',db=self.database_name, port=3306)
            cur = conn.cursor()
            cur.close()
            conn.close()
        except:
            # print traceback.print_exc()
            pass
    ## DEF
    
    def configure_settings(self):
        pass
        ## WITH
    ## DEF
    
    def install_requirements(self, requirement_files):
        pass
    ## DEF

    def get_urls(self):
        pass
    ## DEF

    def sync_server(self, path):
        pass
    ## DEF

    def run_server(self, path):
        pass
    ## DEF

    def try_deploy(self, attempt, deploy_path):
        LOG.info('Configuring settings ...')
        self.kill_server()
        self.clear_database()
        self.configure_settings()

        attempt.database = self.get_database(self.setting_path)
        LOG.info('Database: ' + attempt.database.name)

        LOG.info('Installing requirements ...')

        self.run_server(deploy_path)
        time.sleep(5)
        attemptStatus = self.check_server(self.get_urls())

        return attemptStatus
    ## DEF
    
    def deploy_repo_attempt(self, attempt, deploy_path):
        return self.try_deploy(attempt, deploy_path)
    ## DEF
    
## CLASS
