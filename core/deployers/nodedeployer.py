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
## NODE.JS DEPLOYER
## =====================================================================
class NodeDeployer(BaseDeployer):
    def __init__(self, repo, database, deploy_id, database_config = None):
        BaseDeployer.__init__(self, repo, database, deploy_id, database_config)
        if database_config == None:
            self.database_config['name'] = 'node_app' + str(deploy_id)
        self.main_filename = None
    ## DEF
    
    def configure_settings(self, path):
        utils.replace_files_regex(path, "mysql\.createConnection\({.*?}.*?\);", 
            """mysql.createConnection({{
                host     : '{host}',
                port     : '{port}',
                user     : '{user}',
                password : '{password}',
                database : '{database}'
                }});
            """.format(host=self.database_config['host'], port=self.database_config['port'], 
                user=self.database_config['username'],password=self.database_config['password'],
                database=self.database_config['name']))
    ## DEF
    
    def install_requirements(self, path):
        if path:
            command = '{} && npm install'.format(utils.cd(path))
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
        command = '{} && node {}'.format(
            utils.cd(path), self.main_filename)
        return utils.run_command_async(command)
    ## DEF

    def get_runtime(self):
        out = utils.run_command('node -v')
        return {
            'executable': 'node',
            'version': out[1][1:]
        }
    ## DEF

    def find_port(self):
        out = utils.run_command('netstat -nlp | grep -i "node"')
        port = re.search('0 :::(\d+)', out[1])
        if port:
            self.port = port.group(1)

    def create_tables(self, deploy_path):
        executed = False
        sql_files = utils.search_file_regex(deploy_path, '.*\.sql')
        conn = self.get_database_connection()
        cur = conn.cursor()
        for sql_file in sql_files:
            executed = True
            for statement in open(sql_file).read().split(';'):
                try:
                    cur.execute(statement)
                except Exception, e:
                    print statement
                    LOG.exception(e)
        if self.database.name == 'MySQL':
            conn.commit()
        return executed

    def try_deploy(self, deploy_path):
        LOG.info('Configuring settings ...')
        self.kill_server()
        self.clear_database()
        self.configure_settings(deploy_path)
        self.runtime = self.get_runtime()
        LOG.info(self.runtime)

        self.attempt.database = self.get_database()
        LOG.info('Database: ' + self.attempt.database.name)

        LOG.info('Create Tables ...')
        try:
            if not self.create_tables(deploy_path):
                LOG.error('No sql file found!')
                return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        except Exception, e:
            LOG.exception(e)

        LOG.info('Installing requirements ...')
        out = self.install_requirements(deploy_path)
        lines = out.split('\n')
        packages = {}
        for line in lines:
            s = re.search('(.+?)@([0-9\.]+)', line)
            if s:
                name, version = s.group(1), s.group(2)
                name = name.split(' ')[-1]
                packages[name] = version

        for name, version in packages.iteritems():
            try:
                pkg, created = Package.objects.get_or_create(name=name, version=version, project_type=self.repo.project_type)
                self.packages_from_file.append(pkg)
            except Exception, e:
                LOG.exception(e)

        self.run_server(deploy_path)
        time.sleep(5)

        self.find_port()
        
        attemptStatus = self.check_server()

        return attemptStatus
    ## DEF
    
    def deploy_repo_attempt(self, deploy_path):
        package_jsons = utils.search_file(deploy_path, 'package.json')
        if not package_jsons:
            LOG.error('No package.json found!')
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        base_dir = sorted([os.path.dirname(package_json) for package_json in package_jsons])[0]

        for main_filename in ['server.js', 'app.js', 'main.js']:
            if utils.search_file_norecur(base_dir, main_filename):
                self.main_filename = main_filename
                break
        if self.main_filename == None:
            LOG.error('No main file found!')
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES

        self.setting_path = base_dir

        return self.try_deploy(base_dir)
    ## DEF
    
## CLASS