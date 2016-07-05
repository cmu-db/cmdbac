import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import socket
import urlparse
from StringIO import StringIO
from string import Template
from datetime import datetime
import re

import utils
from cmudbac.settings import *
from library.models import *

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()
streamHandler = logging.StreamHandler()
LOG_formatter = logging.Formatter(fmt='%(asctime)s [%(filename)s:%(funcName)s:%(lineno)03d] %(levelname)-5s: %(message)s',
                                  datefmt='%m-%d-%Y %H:%M:%S')
streamHandler.setFormatter(LOG_formatter)
LOG.addHandler(streamHandler)
LOG.setLevel(logging.INFO)

## =====================================================================
## BASE DEPLOYER
## =====================================================================
class BaseDeployer(object):
    TMP_ZIP_FILE = "tmp.zip"
    TMP_DEPLOY_PATH = "/tmp/crawler"
    
    def __init__(self, repo, database, deploy_id, database_config = None):
        self.repo = repo
        self.database = database
        self.requirement_files = None
        self.packages_from_database = []
        self.packages_from_file = []
        self.deploy_id = deploy_id
        self.zip_file = self.TMP_ZIP_FILE + str(self.deploy_id)
        self.base_path = self.TMP_DEPLOY_PATH + str(self.deploy_id)
        self.setting_path = None
        if self.repo == None:
            self.port = 8000 + int(self.deploy_id)
        else:
            self.port = int(self.repo.project_type.default_port) + int(self.deploy_id)
        self.log_file = None
        self.runtime = None

        # add file handler to LOG
        try:
            fileHandler = logging.FileHandler(os.path.join('/vagrant', str(self.deploy_id) + '.log'), 'w')
            fileHandler.setFormatter(LOG_formatter)
            LOG.addHandler(fileHandler)
        except Exception, e:
            LOG.exception(e)  

        if database_config == None:
            if self.database.name == 'MySQL':
                self.database_config = {
                    'host': '127.0.0.1',
                    'port': 3306,
                    'username': 'root',
                    'password': 'root'
                }
            elif self.database.name == 'PostgreSQL':
                self.database_config = {
                    'host': '127.0.0.1',
                    'port': 5432,
                    'username': 'postgres',
                    'password': 'postgres'
                }
            elif self.database.name == 'SQLite3':
                self.database_config = {
                    'host': '127.0.0.1',
                    'port': '',
                    'username': '',
                    'password': ''
                }
        else:
            self.database_config = database_config

        # Create a buffer so that we can capture all log commands to include in the database for this attempt
        self.log = logging.getLogger()
        self.buffer = StringIO()
        self.logHandler = logging.StreamHandler(self.buffer)
        self.logHandler.setFormatter(LOG_formatter)
        self.log.addHandler(self.logHandler)    
    ## DEF
    
    def get_database(self):
        return self.database
    ## DEF

    def get_database_name(self):
        return self.database_config['name']

    def get_database_connection(self, specify_database = True):
        try:
            if self.database.name == 'MySQL':
                import MySQLdb
                if specify_database:
                    conn = MySQLdb.connect(host=self.database_config['host'],
                                           user=self.database_config['username'],
                                           passwd=self.database_config['password'],
                                           port=self.database_config['port'],
                                           db=self.database_config['name'])
                else:
                    conn = MySQLdb.connect(host=self.database_config['host'],
                                           user=self.database_config['username'],
                                           passwd=self.database_config['password'],
                                           port=self.database_config['port'])
            elif self.database.name == 'PostgreSQL':
                import psycopg2
                if specify_database:
                    conn = psycopg2.connect(host=self.database_config['host'],
                                           user=self.database_config['username'],
                                           password=self.database_config['password'],
                                           port=self.database_config['port'],
                                           database=self.database_config['name'])
                else:
                    conn = psycopg2.connect(host=self.database_config['host'],
                                            user=self.database_config['username'],
                                            password=self.database_config['password'],
                                            port=self.database_config['port'])
            elif self.database.name == 'SQLite3':
                import sqlite3
                conn = sqlite3.connect(self.database_config['name'])
            return conn
        except Exception, e:
            LOG.exception(e)
    ## DEF
    
    def clear_database(self):
        try:
            conn = self.get_database_connection(False)
            if self.database.name == 'SQLite3':
                conn.close()
                return
            if self.database.name == 'PostgreSQL':
                conn.set_isolation_level(0)
            cur = conn.cursor()
            cur.execute('drop database if exists {}'.format(self.database_config['name']))
            cur.execute('create database {}'.format(self.database_config['name']))
            if self.database.name == 'PostgreSQL':
                conn.set_isolation_level(1)
            elif self.database.name == 'MySQL':
                conn.commit()
            cur.close()
            conn.close()
        except Exception, e:
            LOG.exception(e)
    ## DEF

    def get_latest_successful_attempt(self):
        return self.repo.latest_successful_attempt
    ## DEF

    def get_main_url(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF

    def configure_network(self):
        LOG.info('Configuring network ...')
        utils.block_network()
    ## DEF

    def run_server(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF

    def deploy_repo_attempt(self, attempt, path):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF

    def get_runtime(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    ## DEF

    def flush_log(self):
        # stop capturing the log
        self.log.removeHandler(self.logHandler)
        self.logHandler.flush()
        self.buffer.flush()
        self.attempt.log = self.buffer.getvalue()

    def save_attempt(self, attempt_result, driver_result = {}):
        LOG.info("Saving attempt ...")

        # flush log
        self.flush_log()

        # get info
        register_result = driver_result.get('register', USER_STATUS_UNKNOWN)
        login_result = driver_result.get('login', USER_STATUS_UNKNOWN)
        forms = driver_result.get('forms', None)
        urls = driver_result.get('urls', None)
        screenshot_path = driver_result.get('screenshot', None)
        statistics = driver_result.get('statistics', None)
        informations = driver_result.get('informations', None)

        # get runtime
        if self.runtime == None:
            self.runtime = self.get_runtime()
        Runtime.objects.get_or_create(executable = self.runtime['executable'], version = self.runtime['version'])
        runtime = Runtime.objects.get(executable = self.runtime['executable'], version = self.runtime['version'])

        # save attempt
        self.attempt.result = attempt_result
        self.attempt.login = login_result
        self.attempt.register = register_result
        self.attempt.stop_time = datetime.now()
        self.attempt.size = utils.get_size(self.base_path)
        self.attempt.runtime = runtime
        self.attempt.actions_count = 0
        self.attempt.queries_count = 0
        if forms == None and urls == None and self.attempt.result == ATTEMPT_STATUS_SUCCESS:
            self.attempt.result = ATTEMPT_STATUS_NO_QUERIES

        self.attempt.save()

        # save forms
        if forms != None:
            url_patterns = set()
            for f in forms:
                try:
                    if '/admin' in f['url']:
                        continue
                    url_pattern = re.sub('\d', '', f['url'])
                    if url_pattern in url_patterns:
                        continue
                    url_patterns.add(url_pattern)
                    action = Action()
                    action.url = f['url']
                    if f['method'] == '':
                        f['method'] = 'get'
                    action.method = f['method'].upper()
                    action.attempt = self.attempt
                    action.save()
                    self.attempt.actions_count += 1
                    for q in f['queries']:
                        try:
                            query = Query()
                            query.content = q['content']
                            query.matched = q['matched']
                            query.action = action
                            query.save()
                            self.attempt.queries_count += 1

                            if 'explain' in q:
                                explain = Explain()
                                explain.output = q['explain']
                                explain.query = query
                                explain.save()
                        except:
                            pass
                    for input in f['inputs']:
                        field = Field()
                        field.name = input['name']
                        field.type = input['type']
                        field.action = action
                        field.save()
                    for description, count in f['counter'].iteritems():
                        counter = Counter()
                        counter.description = description
                        counter.count = count
                        counter.action = action
                        counter.save()
                except Exception, e:
                    LOG.exception(e)  

        # save urls
        if urls != None:
            url_patterns = set()
            for u in urls:
                try:
                    if '/admin' in u['url']:
                        continue
                    url_pattern = re.sub('\d', '', u['url'])
                    if url_pattern in url_patterns:
                        continue
                    url_patterns.add(url_pattern)
                    action = Action()
                    action.url = u['url']
                    action.method = 'GET'
                    action.attempt = self.attempt
                    action.save()
                    self.attempt.actions_count += 1
                    for q in u['queries']:
                        try:
                            query = Query()
                            query.content = q['content']
                            query.action = action
                            query.save()
                            self.attempt.queries_count += 1

                            if 'explain' in q:
                                explain = Explain()
                                explain.output = q['explain']
                                explain.query = query
                                explain.save()
                        except:
                            pass
                    for description, count in u['counter'].iteritems():
                        counter = Counter()
                        counter.description = description
                        counter.count = count
                        counter.action = action
                        counter.save()
                except Exception, e:
                    LOG.exception(e)  

        # save screenshot
        if screenshot_path != None:
            screenshot = open(screenshot_path, 'rb')
            image = Image()
            image.data = screenshot.read()
            image.attempt = self.attempt
            image.save()

        # save statistics
        if statistics != None:
            for description, count in statistics.iteritems():
                statistic = Statistic()
                statistic.description = description
                statistic.count = count
                statistic.attempt = self.attempt
                statistic.save()

        # save informations
        if informations != None:
            for name, description in informations.iteritems():
                information = Information()
                information.name = name
                information.description = description
                information.attempt = self.attempt
                information.save()

        LOG.info("Saved Attempt #%s for %s" % (self.attempt, self.attempt.repo))
        
        # populate packages
        for pkg in self.packages_from_file:
            try:
                Dependency.objects.get_or_create(attempt=self.attempt, package=pkg, source=PACKAGE_SOURCE_FILE)
                pkg.count = pkg.count + 1
                pkg.save()
            except Exception, e:
                LOG.exception(e)  
        ## FOR
        for pkg in self.packages_from_database:
            try:
                Dependency.objects.get_or_create(attempt=self.attempt, package=pkg, source=PACKAGE_SOURCE_DATABASE)
                if pkg.version != '':
                    pkg.count = pkg.count + 1
                    pkg.save()
            except Exception, e:
                LOG.exception(e)
        ## FOR

        # make sure we update the repo to point to this latest attempt
        if attempt_result in [ATTEMPT_STATUS_MISSING_REQUIRED_FILES, ATTEMPT_STATUS_RUNNING_ERROR, ATTEMPT_STATUS_DOWNLOAD_ERROR]:
            self.repo.valid_project = False
        else:
            self.repo.valid_project = True
        self.repo.latest_attempt = self.attempt
        if self.attempt.result == ATTEMPT_STATUS_SUCCESS and self.attempt.queries_count == 0:
            self.attempt.result = ATTEMPT_STATUS_NO_QUERIES
        if self.attempt.result == ATTEMPT_STATUS_SUCCESS:
            self.repo.latest_successful_attempt = self.attempt
        self.repo.attempts_count = self.repo.attempts_count + 1
        self.repo.save()
        self.attempt.save()
    ## DEF

    def deploy(self, attempt_info = None):
        self.attempt_info = attempt_info
        if attempt_info:
            repo_name = attempt_info['repo_info']['name']
            self.database = Database()
            self.database.name = attempt_info['database_info']['name']
        else:
            repo_name = self.repo.name
        LOG.info('Deploying Repository: {} ...'.format(repo_name))
        
        self.attempt = Attempt()
        if self.repo:
            self.attempt.repo = self.repo
        if self.database:
            self.attempt.database = self.database
        self.attempt.start_time = datetime.now()
        self.attempt.hostname = socket.gethostname()

        if attempt_info:
            crawler_class = {
                1: "GitHubCrawler",
                2: "DrupalCrawler"
            }[attempt_info['repo_info']['source']]
            crawler = utils.get_crawler(None, crawler_class)
        else:
            crawler_status = CrawlerStatus.objects.get(id=1)
            crawler = utils.get_crawler(crawler_status, self.repo.source.crawler_class)

        LOG.info('Validating Repository ...')
        try:
            self.attempt.sha = crawler.get_latest_sha(repo_name)
        except Exception, e:
            LOG.exception(e)
            if not attempt_info:
                self.save_attempt(ATTEMPT_STATUS_DOWNLOAD_ERROR)
            LOG.error('Download Error..')
            return -1

        LOG.info('Downloading Repository ...'.format(self.attempt.sha))
        try:
            crawler.download_repository(repo_name, self.attempt.sha, self.zip_file)
        except Exception, e:
            LOG.exception(e)
            if not attempt_info:
                self.save_attempt(ATTEMPT_STATUS_DOWNLOAD_ERROR)
            else:
                LOG.error('Download Error..')
            return -1
        
        try:
            utils.make_dir(self.base_path)
            utils.unzip(self.zip_file, self.base_path)
        except Exception, e:
            LOG.exception(e)
            if not attempt_info:
                self.save_attempt(ATTEMPT_STATUS_DOWNLOAD_ERROR)
            else:
                LOG.error('Download Error..')
            return -1

        LOG.info('Deploying at {} ...'.format(self.base_path))

        try:
            attemptStatus = self.deploy_repo_attempt(self.base_path)
        except Exception, e:
            LOG.exception(e)
            if not attempt_info:
                self.save_attempt(ATTEMPT_STATUS_RUNNING_ERROR)
            else:
                LOG.error('Running Error...')
            return -1
           
        if attemptStatus != ATTEMPT_STATUS_SUCCESS:
            if not attempt_info:
                self.save_attempt(attemptStatus)
            return -1
        
        return 0
    ## DEF

    def check_server(self):
        LOG.info("Checking server ...")
        url = self.get_main_url()
        LOG.info("Main Url : {}".format(url))
        command = 'wget --spider {}'.format(url)
        out = utils.run_command(command)
        LOG.info(out)
        if not "200 OK" in out[2]:
            return ATTEMPT_STATUS_RUNNING_ERROR
        else:
            return ATTEMPT_STATUS_SUCCESS
    ## DEF

    def kill_server(self):
        LOG.info('Killing server on port {} ...'.format(self.port))
        utils.kill_port(self.port)
        utils.unblock_network()
        return
    ## DEF
    
## CLASS
