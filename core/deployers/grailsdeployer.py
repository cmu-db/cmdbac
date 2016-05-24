import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import re
import time

from basedeployer import BaseDeployer
from library.models import *
from cmudbac.settings import *
import utils

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## =====================================================================
## SETTINGS
## =====================================================================
DATABASE_SETTINGS = """
dataSource {{
    pooled = true
    jmxExport = true
    driverClassName = "{jdbc_class}"
    url = "jdbc:{adapter}://{host}/{name}"
    username = "{username}"
    password = "{password}"
    dbCreate = "create"
}}

hibernate {{
    cache.use_second_level_cache = true
    cache.use_query_cache = true
    cache.region.factory_class = 'net.sf.ehcache.hibernate.EhCacheRegionFactory' // Hibernate 3
    //cache.region.factory_class = 'org.hibernate.cache.ehcache.EhCacheRegionFactory' // Hibernate 4
    singleSession = true // configure OSIV singleSession mode
    //flush.mode = 'manual' // OSIV session flush mode outside of transactional context

    cache.use_minimal_puts=false
    cache.provider_configuration_file_resource_path='/ehcache-hibernate.xml'

    default_batch_fetch_size=32
    jdbc.batch_size=32
    jdbc.fetch_size=256
}}
"""
REPOSITORIES_SETTINGS = """
mavenRepo "http://repo.grails.org/grails/core"
mavenRepo "http://repo.grails.org/grails/plugins"
"""

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
    
    def configure_settings(self):
        if HTTP_PROXY != '':
            with open(os.path.join(self.setting_path, 'wrapper', 'grails-wrapper.properties'), "a") as my_file:
                my_file.write('\n')
                proxy_host, proxy_port = HTTP_PROXY.split(':')
                my_file.write('systemProp.http.proxyHost={}\n'.format(proxy_host))
                my_file.write('systemProp.http.proxyPort={}\n'.format(proxy_port))
                my_file.write('systemProp.http.nonProxyHosts=localhost,127.0.0.1')

        adapter = {
            'MySQL': 'mysql',
        }[self.database.name]

        jdbc_class = {
            'MySQL': 'com.mysql.jdbc.Driver'
        }[self.database.name]

        with open(os.path.join(self.setting_path, 'grails-app', 'conf', 'DataSource.groovy'), "w") as my_file:
            my_file.write(DATABASE_SETTINGS.format(name=self.database_config['name'], 
                username=self.database_config['username'], password=self.database_config['password'],
                host=self.database_config['host'], adapter=adapter, jdbc_class = jdbc_class))

        with open(os.path.join(self.setting_path, 'grails-app', 'conf', 'BuildConfig.groovy'), "r") as my_file:
            build_config = my_file.read()
        with open(os.path.join(self.setting_path, 'grails-app', 'conf', 'BuildConfig.groovy'), "w") as my_file:
            def add_repositories(matched):
                s = matched.group(0)
                s = s[:-1] + REPOSITORIES_SETTINGS + "}"
                return s
            my_file.write(re.sub("repositories.*?{.*?}", add_repositories, build_config, flags = re.S))
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
        self.configure_settings()
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
        if self.database.name != 'MySQL':
            return ATTEMPT_STATUS_DATABASE_ERROR

        grailsw_files = utils.search_file(deploy_path, 'grailsw')
        if not grailsw_files:
            LOG.error('No grailsw found!')
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        base_dir = sorted([os.path.dirname(grailsw_file) for grailsw_file in grailsw_files])[0]

        self.setting_path = base_dir

        return self.try_deploy(base_dir)
    ## DEF
    
## CLASS