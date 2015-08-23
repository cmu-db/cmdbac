import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
import re
import time

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
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'crawler',
        'HOST': '10.0.2.2',
        'PORT': '3306',
        'USER': 'root',
        'PASSWORD': '',
    }
}
"""

## =====================================================================
## DJANGO DEPLOYER
## =====================================================================
class DjangoDeployer(BaseDeployer):
    def __init__(self, repo, database):
        BaseDeployer.__init__(self, repo, database)
        self.setting_file = None
    ## DEF
    
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
    
    def configure_settings(self, settings_file):
        with open(settings_file, "a") as my_file:
            my_file.write(DJANGO_SETTINGS)
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
    
    def get_urls(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
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

        self.requirement_files = utils.search_file(deploy_path, 'requirements.txt')
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
        
        return self.try_deploy(attempt, manage_path, setting_file)
    ## DEF
    
    def try_deploy(self, attempt, deploy_path, setting_path):
        LOG.info('Configuring settings ...')
        self.configure_settings(setting_path)
        self.kill_server()

        LOG.info('Installing requirements ...')
        self.installed_requirements = []
        self.packages_from_database = []
        packages = self.install_requirements(self.requirement_files)
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
            LOG.info('Syncing server ...')
            out = self.sync_server(deploy_path)
            # TODO: when sync error
            if out[0] != 0:
                LOG.info(out)
                break
            out = out[1].strip()
            out = out[1].splitlines()
            if out and out[-1].strip().startswith('ImportError'):
                line = out[-1].strip()
                match = re.search('(?<=No module named )\S+', line)
                if match:
                    missing_module_name = match.group(0)
                    LOG.info('missing module: ' + missing_module_name) 
                    if missing_module_name == last_missing_module_name:
                        index = index + 1
                        if index == len(candidate_packages):
                            LOG.info('no more possible package')
                            return ATTEMPT_STATUS_MISSING_DEPENDENCIES
                        out = utils.pip_install([candidate_packages[index]], False)
                        LOG.info('pip install output: ' + out)
                    else:
                        if last_missing_module_name != '':
                            self.packages_from_database.append(candidate_packages[index])
                        candidate_package_ids = Module.objects.filter(name=missing_module_name).values_list('package_id', flat=True)
                        if not candidate_package_ids:
                            LOG.info('no possible package')
                            return ATTEMPT_STATUS_MISSING_DEPENDENCIES
                        last_missing_module_name = missing_module_name
                        #packages_from_file = [pkg for pkg in packages_from_file if pkg.id not in pckage_ids]
                        candidate_packages = Package.objects.filter(id__in=candidate_package_ids).order_by('-count', 'name', '-version')
                        LOG.info('candidate packages: ' + str(candidate_packages))
                        index = 0
                        out = utils.pip_install([candidate_packages[0]], False)
                        LOG.info('pip install output: ' + out)
                else:
                    return ATTEMPT_STATUS_MISSING_DEPENDENCIES
            else:
                if last_missing_module_name != '':
                    self.packages_from_database.append(candidate_packages[index])
                break
        ## FOR
        
        LOG.info('Running server ...')
        result = self.run_server(deploy_path)

        time.sleep(1)
        LOG.info('Checking server ...')
        attemptStatus = self.check_server()

        result.get()

        return attemptStatus
    ## DEF
    
    def run_server(self, path):
        command = '{} && unset DJANGO_SETTINGS_MODULE && python manage.py runserver 0.0.0.0:{}'.format(
            utils.cd(path), 
            self.repo.project_type.default_port)
        return utils.run_command_async(command, 5)
    ## DEF
    
    def sync_server(self, path):
        command = '{} && unset DJANGO_SETTINGS_MODULE && python manage.py syncdb --noinput'.format(
            utils.cd(path))
        return utils.run_command(command)
    ## DEF
    
## CLASS
