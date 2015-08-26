import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
import re
import time
import importlib
import traceback
import MySQLdb

from django.db import connection

from basedeployer import BaseDeployer
from crawler.models import *
import utils

from multiprocessing import Pool

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## =====================================================================
## SETTINGS
## =====================================================================
DJANGO_SETTINGS = """
SECRET_KEY = 'abcdefghijklmnopqrstuvwxyz'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '{}',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'USER': 'root',
        'PASSWORD': 'root',
    }}
}}
"""

## =====================================================================
## DJANGO DEPLOYER
## =====================================================================
class DjangoDeployer(BaseDeployer):
    def __init__(self, repo, database):
        BaseDeployer.__init__(self, repo, database)
        self.database_name = 'django_app'
    ## DEF
    
    # TODO : fix
    def get_database(self, settings_file):
        regexes = [
            re.compile(r'django\.db\.backends\.([\w\d]+)'),
            re.compile('adapter\s*:\s*([\w\d]+)')
        ]
        db = Database(name="Unknown")
        with open(settings_file, 'r') as infile:
            for regex in regexes:
                for line in infile:
                    p = regex.search(line);
                    if p:
                        dbName = p.group(1).lower()
                        if dbName == "sqlite": dbName = "sqlite3" # HACK
                        db = Database.objects.get(name__iexact=dbName)
                        if not db is None:
                            break
                ## FOR
                if not db is None:
                    break
            ## FOR
        ## WITH
        return db
    ## DEF

    def clear_database(self):
        try:
            conn = MySQLdb.connect(host='localhost',user='root',passwd='root',port=3306)
            cur = conn.cursor()
            cur.execute('drop database if exists {}'.format(self.database_name))
            cur.execute('create database {}'.format(self.database_name))
            conn.commit()
            cur.close()
            conn.close()
        except:
            print traceback.print_exc()
    ## DEF

    def extract_database_info(self):
        try:
            conn = MySQLdb.connect(host='localhost',user='root',passwd='root',db=self.database_name, port=3306)
            cur = conn.cursor()
            cur.close()
            conn.close()
        except:
            print traceback.print_exc()
    ## DEF
    
    def configure_settings(self, settings_file):
        with open(settings_file, "a") as my_file:
            my_file.write(DJANGO_SETTINGS.format(self.database_name))
        ## WITH
    ## DEF
    
    def install_requirements(self, requirement_files):
        if requirement_files:
            utils.pip_clear()
            old_packages = utils.pip_freeze()
            for requirement_file in requirement_files:
                out = utils.pip_install(requirement_file, True)
            new_packages = utils.pip_freeze()
            diff_packages = list(set(new_packages) - set(old_packages))
            return diff_packages
        else:
            return []
    ## DEF
    
    def get_urls(self, setting_path):
        sys.path.append(os.path.join(os.path.dirname(setting_path), os.pardir))
        app_name = os.path.split(os.path.dirname(setting_path))[-1]
        urls_module = importlib.import_module('{}.urls'.format(app_name))

        urls = []
        def get_urls_rec(urllist, url):
            for entry in urllist:
                new_entry = entry.regex.pattern
                new_url = os.path.join(url, new_entry)
                if hasattr(entry, 'url_patterns'):
                    get_urls_rec(entry.url_patterns, new_url)
                else:
                    urls.append(new_url)

        get_urls_rec(urls_module.urlpatterns, '')

        urls = list(set([re.sub(r'[\^\$]', '', url) for url in urls if '?' not in url]))
        urls = sorted(urls, key=len)

        return urls
    ## DEF

    def sync_server(self, path):
        LOG.info('Syncing server ...')
        command = '{} && unset DJANGO_SETTINGS_MODULE && python manage.py syncdb --noinput'.format(
            utils.cd(path))
        return utils.run_command(command)
    ## DEF

    def run_server(self, path):
        LOG.info('Running server ...')
        command = '{} && unset DJANGO_SETTINGS_MODULE && python manage.py runserver 127.0.0.1:{}'.format(
            utils.cd(path), 
            self.repo.project_type.default_port)
        return utils.run_command_async(command)
    ## DEF

    def try_deploy(self, attempt, deploy_path, setting_path, requirement_files):
        LOG.info('Configuring settings ...')
        self.kill_server()
        self.clear_database()
        self.configure_settings(setting_path)

        LOG.info('Installing requirements ...')
        self.installed_requirements = []
        self.packages_from_database = []
        packages = self.install_requirements(requirement_files)
        for package in packages:
            name, version = package.split('==')
            pkg, created = Package.objects.get_or_create(name=name, version=version, project_type=self.repo.project_type)
            self.installed_requirements.append(pkg)
        ## FOR
        LOG.info('Installed requirements: {}'.format(self.installed_requirements))

        threshold = 10
        last_missing_module_name = ''
        index = 0
        for tmp in range(threshold):
            out = self.sync_server(deploy_path)
            # TODO: when sync error
            if out[0] != 0:
                LOG.info(out)
            out = out[2].strip().splitlines()
            if out and out[-1].strip().startswith('ImportError'):
                line = out[-1].strip()
                match = re.search('(?<=No module named )\S+', line)
                if match:
                    missing_module_name = match.group(0)
                    LOG.info('Missing module: ' + missing_module_name) 
                    if missing_module_name == last_missing_module_name:
                        index = index + 1
                        if index == len(candidate_packages):
                            LOG.info('No more possible packages!')
                            return ATTEMPT_STATUS_MISSING_DEPENDENCIES
                        out = utils.pip_install([candidate_packages[index]], False)
                        LOG.info('pip install output: {}'.format(out))
                    else:
                        if last_missing_module_name != '':
                            self.packages_from_database.append(candidate_packages[index])
                        candidate_package_ids = Module.objects.filter(name=missing_module_name).values_list('package_id', flat=True)
                        if not candidate_package_ids:
                            LOG.info('No possible packages!')
                            return ATTEMPT_STATUS_MISSING_DEPENDENCIES
                        last_missing_module_name = missing_module_name
                        candidate_packages = Package.objects.filter(id__in=candidate_package_ids).order_by('-count', 'name', '-version')
                        LOG.info('Candidate packages: {}'.format(candidate_packages))
                        index = 0
                        out = utils.pip_install([candidate_packages[0]], False)
                        LOG.info('pip install output: {}'.format(out))
                else:
                    return ATTEMPT_STATUS_MISSING_DEPENDENCIES
            else:
                if last_missing_module_name != '':
                    self.packages_from_database.append(candidate_packages[index])
                break
        ## FOR
        
        result, p = self.run_server(deploy_path)

        time.sleep(1)
        attemptStatus = self.check_server(self.get_urls(setting_path))

        p.close()

        return attemptStatus
    ## DEF
    
    def deploy_repo_attempt(self, attempt, deploy_path):
        utils.pip_clear()

        setup_files = utils.search_file(deploy_path, 'setup.py')
        LOG.info('setup.py: {}'.format(setup_files))
        if setup_files:
            return ATTEMPT_STATUS_NOT_AN_APPLICATION

        setting_files = utils.search_file(deploy_path, 'settings.py')
        LOG.info('settings.py: {}'.format(setting_files))
        if not setting_files:
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
                
        manage_files = utils.search_file(deploy_path, 'manage.py')
        # LOG.info('manage.py: {}'.format(manage_files))
        if not manage_files:
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES

        requirement_files = utils.search_file(deploy_path, 'requirements.txt')
        #LOG.info('requirements.txt: {}'.format(self.requirement_files))
        
        manage_paths = [os.path.dirname(manage_file) for manage_file in manage_files]
        # LOG.info('Manage path: {}'.format(manage_paths))
        setting_paths = [os.path.dirname(os.path.dirname(setting_file)) for setting_file in setting_files]
        # LOG.info('Setting path: {}'.format(setting_paths))
        base_dirs = set.intersection(set(manage_paths), set(setting_paths))
        if not base_dirs:
            LOG.error('Can not find base directory!')
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        base_dir = next(iter(base_dirs))
        LOG.info('Base directory: ' + base_dir)
        manage_path = next(name for name in manage_paths if name.startswith(base_dir))
        setting_file = next(name for name in setting_files if name.startswith(base_dir))
        
        attempt.base_dir = base_dir.split('/', 1)[1]
        # LOG.info('BASE_DIR: ' + attempt.base_dir)

        attempt.database = self.get_database(setting_file)
        LOG.info('Database: ' + attempt.database.name)
        
        attempt.setting_dir = os.path.basename(os.path.dirname(setting_file))
        # LOG.info('SETTING_DIR: ' + attempt.setting_dir)
        
        return self.try_deploy(attempt, manage_path, setting_file, requirement_files)
    ## DEF
    
## CLASS
