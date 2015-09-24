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
        'PASSWORD': 'root'
    }}
}}
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/crawler'
REGISTRATION_CAPTCHA = False
"""

## =====================================================================
## DJANGO DEPLOYER
## =====================================================================
class DjangoDeployer(BaseDeployer):
    def __init__(self, repo, database):
        BaseDeployer.__init__(self, repo, database)
        self.database_name = 'django_app'
        self.setting_path = None
        self.requirement_files = None
    ## DEF
    
    def get_database(self, setting_file):
        regexes = [
            re.compile(r'django\.db\.backends\.([\w\d]+)'),
            re.compile('adapter\s*:\s*([\w\d]+)')
        ]
        db = Database(name="Unknown")
        with open(setting_file, 'r') as infile:
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
        with open(self.setting_path, "a") as my_setting_file:
            my_setting_file.write(DJANGO_SETTINGS.format(self.database_name))
        ## WITH
        for requirement_file in self.requirement_files:
            with open(requirement_file, "r") as my_requirement_file:
                requirements = my_requirement_file.read()
                requirements = re.sub('mysql-python==.*', '', requirements, flags=re.IGNORECASE)
                fout = open(requirement_file, 'w')
                fout.write(requirements)
                fout.flush()
                fout.close()
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

    def get_urls(self):
        sys.path.append(os.path.join(os.path.dirname(self.setting_path), os.pardir))
        app_name = os.path.split(os.path.dirname(self.setting_path))[-1]
        try:
            urls_module = importlib.import_module('{}.urls'.format(app_name))
        except:
            return ['']

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
        command = '{} && unset DJANGO_SETTINGS_MODULE && python manage.py migrate'.format(
            utils.cd(path))
        return utils.run_command(command)
    ## DEF

    def create_superuser(self, path):
        LOG.info('Creating superuser ...')
        command = '{} && unset DJANGO_SETTINGS_MODULE && {}'.format(
            utils.cd(path),
            """
            echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@test.com', 'admin')" | python manage.py shell
            """)
        return utils.run_command(command)
    ## DEF

    def run_server(self, path):
        self.configure_network()
        LOG.info('Running server ...')
        command = '{} && unset DJANGO_SETTINGS_MODULE && python manage.py runserver 0.0.0.0:{}'.format(
            utils.cd(path), 
            self.repo.project_type.default_port)
        return utils.run_command_async(command)
    ## DEF

    def try_deploy(self, attempt, deploy_path, requirement_files):
        LOG.info('Configuring settings ...')
        self.kill_server()
        self.clear_database()
        self.configure_settings()

        attempt.database = self.get_database(self.setting_path)
        LOG.info('Database: ' + attempt.database.name)

        LOG.info('Installing requirements ...')
        self.installed_requirements = []
        self.packages_from_database = []
        packages = self.install_requirements(requirement_files)
        for package in packages:
            name, version = package.split('==')
            try:
                pkg, created = Package.objects.get_or_create(name=name, version=version, project_type=self.repo.project_type)
                self.installed_requirements.append(pkg)
            except:
                # print traceback.print_exc()
                pass
        ## FOR
        LOG.info('Installed requirements: {}'.format(self.installed_requirements))

        threshold = 100
        last_missing_module_name = ''
        index = 0
        dependencies = []
        for tmp in range(threshold):
            output = self.sync_server(deploy_path)
            if output[0] != 0:
                LOG.info(output)
            else:
                LOG.info(output)
                break
            split_output = output[2].strip().splitlines()
            if split_output and split_output[-1].strip().startswith('ImportError'):
                line = split_output[-1].strip()
                match = re.search('(?<=No module named )\S+', line)
                if match:
                    missing_module_name = match.group(0)
                    LOG.info('Missing module: ' + missing_module_name)
                    if missing_module_name == last_missing_module_name:
                        missing_module_name, candidate_packages, index = dependencies[-1]
                        index = index + 1
                        if index < len(candidate_packages):
                            dependencies[-1] = (missing_module_name, candidate_packages, index)
                            pip_output = utils.pip_install([candidate_packages[index]], False)
                            # LOG.info('pip install output: {}'.format(pip_output))
                        elif index == len(candidate_packages):
                            output = utils.pip_install([candidate_packages[index - 1]], False, False)
                            # LOG.info('pip install output: {}'.format(output))    
                        else:
                            # LOG.info('No more possible packages!')
                            return ATTEMPT_STATUS_MISSING_DEPENDENCIES
                    else:
                        candidate_package_ids = Module.objects.filter(name=missing_module_name).values_list('package_id', flat=True)
                        if not candidate_package_ids:
                            LOG.info('No possible packages!')
                            return ATTEMPT_STATUS_MISSING_DEPENDENCIES
                        last_missing_module_name = missing_module_name
                        candidate_packages = Package.objects.filter(id__in=candidate_package_ids).order_by('-count', 'name', '-version')
                        # LOG.info('Candidate packages: {}'.format(candidate_packages))
                        dependencies.append((missing_module_name, candidate_packages, 0))
                        index = 0
                        pip_output = utils.pip_install([candidate_packages[0]], False)
                        # LOG.info('pip install output: {}'.format(pip_output))
                else:
                        matched_candidate_packages = None
                        matched_index = None
                        for dependency_index in range(len(dependencies)):
                            missing_module_name, candidate_packages, index = dependencies[dependency_index]
                            if missing_module_name in output[2].strip():
                                index = index + 1
                                if index < len(candidate_packages):
                                    dependencies[dependency_index] = (missing_module_name, candidate_packages, index)
                                    output = utils.pip_install([candidate_packages[index]], False)
                                    # LOG.info('pip install output: {}'.format(output))
                                elif index == len(candidate_packages):
                                    output = utils.pip_install([candidate_packages[index - 1]], False, False)
                                    # LOG.info('pip install output: {}'.format(output))
                                else:
                                    LOG.info('No more possible packages!')
                                    return ATTEMPT_STATUS_MISSING_DEPENDENCIES
            else:
                match2 = re.search('pip install ([a-zA-Z\-_]+)', output[2].strip())
                if match2:
                    package_name = match2.group(1)
                    output = utils.pip_install_text(package_name)
                    # LOG.info('pip install output: {}'.format(output))
                else:
                    return ATTEMPT_STATUS_MISSING_DEPENDENCIES
        ## FOR

        for missing_module_name, candidate_packages, index in dependencies:
            self.packages_from_database.append(candidate_packages[index])
        
        self.create_superuser(deploy_path)

        result, p = self.run_server(deploy_path)

        time.sleep(5)
        attemptStatus = self.check_server(self.get_urls())
        
        return attemptStatus
    ## DEF
    
    def deploy_repo_attempt(self, attempt, deploy_path):
        utils.pip_clear()

        if 0:
            setup_files = utils.search_file(deploy_path, 'setup.py')
            # LOG.info('setup.py: {}'.format(setup_files))
            if setup_files:
                return ATTEMPT_STATUS_NOT_AN_APPLICATION

        setting_files = utils.search_file(deploy_path, 'settings.py')
        
        if not setting_files:
            for candidate_setting_files in utils.search_file(deploy_path, 'settings_example.py'):
                utils.copy_file(candidate_setting_files, os.path.join(os.path.dirname(candidate_setting_files), "settings.py"))
                break
            setting_files = utils.search_file(deploy_path, 'settings.py')
        
        if not setting_files:
            for candidate_setting_files in utils.search_file_regex(deploy_path, '^settings.*\.py$'):
                utils.copy_file(candidate_setting_files, os.path.join(os.path.dirname(candidate_setting_files), "settings.py"))
                break
            setting_files = utils.search_file(deploy_path, 'settings.py')
        
        if not setting_files:
            return ATTEMPT_STATUS_NOT_AN_APPLICATION

        LOG.info('settings.py: {}'.format(setting_files))

        manage_files = utils.search_file(deploy_path, 'manage.py')
        # LOG.info('manage.py: {}'.format(manage_files))
        if not manage_files:
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES

        requirement_files = utils.search_file(deploy_path, 'requirements.txt')
        #LOG.info('requirements.txt: {}'.format(self.requirement_files))

        self.requirement_files = requirement_files
        
        manage_paths = [os.path.dirname(manage_file) for manage_file in manage_files]
        
        base_dir = next(name for name in manage_paths)
        
        manage_path = next(name for name in manage_paths if name.startswith(base_dir))
        setting_file = next(name for name in setting_files if name.startswith(base_dir))
        
        self.setting_path = setting_file

        attempt.base_dir = base_dir.split('/', 1)[1]
        # LOG.info('BASE_DIR: ' + attempt.base_dir)
        
        attempt.setting_dir = os.path.basename(os.path.dirname(setting_file))
        # LOG.info('SETTING_DIR: ' + attempt.setting_dir)
        
        return self.try_deploy(attempt, manage_path, requirement_files)
    ## DEF

    def kill_server(self):
        utils.pip_clear()
        return super(DjangoDeployer, self).kill_server()
    ## DEF
    
## CLASS
