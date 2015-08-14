import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
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
DJANGO_SETTINGS = """
SECRET_KEY = 'abcdefghijklmnopqrstuvwxyz'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db_webcrawler',
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
    
    def getDatabase(self, settings_file):
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
        return (db)
    ## DEF
    
    def rewrite_settings(self, settings_file):
        with open(settings_file, "a") as my_file:
            my_file.write(DJANGO_SETTINGS)
        ## WITH
    ## DEF
    
    def install_requirements(self, requirement_files):
        if requirement_files:
            utils.vagrant_pip_clear()
            old_packages = utils.vagrant_pip_freeze()
            for requirement_file in requirement_files:
                out = utils.vagrant_pip_install(requirement_file, True)
            new_packages = utils.vagrant_pip_freeze()
            diff_packages = list(set(new_packages) - set(old_packages))
            return diff_packages
        else:
            return []
    ## DEF
    
    def get_urls(self):
        setting_files = utils.search_file(BaseDeployer.TMP_DEPLOY_PATH, 'settings.py')[0]
        dirname = os.path.dirname(setting_files)
        sys.path.append(dirname)
        proj_name = os.path.basename(setting_files)
        command = "python " + utils.to_vm_path('get_urls.py') + ' ' + utils.to_vm_path(dirname) + ' ' + proj_name
        print command
        out = utils.vagrant_run_command(command).strip()
        if not out:
            urls = []
        else:
            urls = out.splitlines()
        return urls
    ## DEF
    
    def deployRepoAttempt(self, attempt, deployPath):
        utils.vagrant_pip_clear()

        setup_files = utils.search_file(deployPath, 'setup.py')
        LOG.info('setup.py: ' + str(setup_files))
        if len(setup_files):
            return ATTEMPT_STATUS_NOT_AN_APPLICATION

        setting_files = utils.search_file(deployPath, 'settings.py')
        LOG.info('settings.py: ' + str(setting_files))
        if not len(setting_files):
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
                
        manage_files = utils.search_file(deployPath, 'manage.py')
        LOG.info('manage.py: ' + str(manage_files))
        if not len(manage_files):
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES

        self.requirement_files = utils.search_file(deployPath, 'requirements.txt')
        LOG.info('REQUIREMENTS: ' + str(self.requirement_files))
        
        manage_paths = [os.path.dirname(manage_file) for manage_file in manage_files]
        LOG.info("MANAGE_PATHS: " + str(manage_paths))
        setting_paths = [os.path.dirname(os.path.dirname(setting_file)) for setting_file in setting_files]
        LOG.info("setting_paths: " + str(setting_paths))
        base_dirs = set.intersection(set(manage_paths), set(setting_paths))
        if not base_dirs:
            LOG.error('can not find base directory')
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        base_dir = next(iter(base_dirs))
        LOG.info('BASE_DIR: ' + base_dir)
        manage_file = next(name for name in manage_files if name.startswith(base_dir))
        setting_file = next(name for name in setting_files if name.startswith(base_dir))

        # Database
        attempt.database = self.getDatabase(setting_file)
        LOG.info('DATABASE: ' + attempt.database.name)
        
        # Base Dir
        attempt.base_dir = base_dir.split('/', 1)[1]
        LOG.info('BASE_DIR: ' + attempt.base_dir)
        
        # Settings Dir
        attempt.setting_dir = os.path.basename(os.path.dirname(setting_file))
        LOG.info('SETTING_DIR: ' + attempt.setting_dir)
        
        # Try to deploy!
        return self.tryDeploy(attempt, manage_file, setting_file)
    ## DEF
    
    def tryDeploy(self, attempt, manage_file, setting_file):
        self.rewrite_settings(setting_file)
        LOG.info('Settings appended')
        self.killServer()

        self.installed_requirements = []
        self.packages_from_database = []

        packages = self.install_requirements(self.requirement_files)
        for package in packages:
            name, version = package.split('==')
            pkg, created = Package.objects.get_or_create(name=name, version=version, project_type=self.repo.project_type)
            self.installed_requirements.append(pkg)
        ## FOR
        LOG.info('INSTALLED_REQUIREMENTS: ' + str(self.installed_requirements))

        threshold = 10
        last_missing_module_name = ''
        index = 0
        #candidate_packages = []
        for tmp in range(threshold):
            out = self.syncServer(manage_file)
            LOG.info('SYNCDB OUTPUT: ' + out) 
            out = out.strip()
            out = out.splitlines()
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
                        out = utils.vagrant_pip_install([candidate_packages[index]], False)
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
                        out = utils.vagrant_pip_install([candidate_packages[0]], False)
                        LOG.info('pip install output: ' + out)
                else:
                    return ATTEMPT_STATUS_MISSING_DEPENDENCIES
            else:
                if last_missing_module_name != '':
                    self.packages_from_database.append(candidate_packages[index])
                break
        
        # Fire away!
        out = self.runServer(manage_file)
        LOG.info(out)
        return ATTEMPT_STATUS_SUCCESS
    ## DEF
    
    def runServer(self, path):
        LOG.info("Run server...")
        vm_manage_file = utils.to_vm_path(path)
        command = utils.vagrant_cd(os.path.dirname(path)) + " && " + \
                  "nohup python manage.py runserver 0.0.0.0:8800 & sleep 1"
        return utils.vagrant_run_command(command)
    ## DEF
    
    def syncServer(self, path):
        LOG.info("Sync server...")
        command = utils.vagrant_cd(os.path.dirname(path)) + " && " + \
                  "python manage.py syncdb --noinput && python manage.py migrate --noinput"
        return utils.vagrant_run_command(command)
    ## DEF
    
## CLASS
