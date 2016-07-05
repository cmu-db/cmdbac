import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import re
import time
import importlib
import urlparse

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
DJANGO_SETTINGS = """
SECRET_KEY = 'abcdefghijklmnopqrstuvwxyz'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.{engine}',
        'NAME': '{name}',
        'HOST': '{host}',
        'PORT': '{port}',
        'USER': '{username}',
        'PASSWORD': '{password}',
        'CONN_MAX_AGE': 500
    }}
}}
LOGGING = {{
    'version': 1,
    'handlers': {{
        'file': {{
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '{log_file}',
        }}
    }},
    'loggers': {{
        'django.db.backends': {{
            'level': 'DEBUG',
            'handlers': ['file']
        }}
    }}
}}
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '{path}'
"""
## =====================================================================
## DJANGO DEPLOYER
## =====================================================================
class DjangoDeployer(BaseDeployer):
    def __init__(self, repo, database, deploy_id, database_config = None):
        BaseDeployer.__init__(self, repo, database, deploy_id, database_config)
        if database_config == None:
            self.database_config['name'] = 'django_app' + str(deploy_id)
        if self.database != None and self.database.name == 'SQLite3':
            self.log_file = os.path.join(self.base_path, 'sql.log')
    ## DEF

    def configure_settings(self):
        engine = {
            'MySQL': 'mysql',
            'PostgreSQL': 'postgresql_psycopg2',
            'SQLite3': 'sqlite3'
        }[self.database.name]
        with open(self.setting_path, "a") as my_setting_file:
            my_setting_file.write(DJANGO_SETTINGS.format(name=self.database_config['name'], 
                host=self.database_config['host'], port=self.database_config['port'], 
                username=self.database_config['username'], password=self.database_config['password'],
                path=self.base_path, engine=engine, log_file=self.log_file))
        ## WITH
    ## DEF
    
    def install_requirements(self, deploy_path, requirement_files):
        ret_packages = []
        if self.attempt_info != None:
            dependencies = self.attempt_info['dependencies']
            for dependency in dependencies:
                LOG.info('pip install {}'.format(dependency['package_info']['name']))
                pip_output = utils.pip_install(self.base_path, [dependency['package_info']], False)
                LOG.info('pip install output: {}'.format(pip_output))
        else:
            latest_successful_attempt = self.get_latest_successful_attempt()
            if latest_successful_attempt != None:
                dependencies = Dependency.objects.filter(attempt = latest_successful_attempt)
                for dependency in dependencies:
                    if dependency.source == PACKAGE_SOURCE_FILE:
                        self.packages_from_file.append(dependency.package)
                    else:
                        self.packages_from_database.append(dependency.package)
                    LOG.info('pip install {}'.format(dependency.package))
                    pip_output = utils.pip_install(self.base_path, [dependency.package], False)
                    LOG.info('pip install output: {}'.format(pip_output))
            else:
                if requirement_files:
                    for requirement_file in requirement_files:
                        out = utils.pip_install(deploy_path, requirement_file, True)
                        with open(requirement_file, "r") as my_requirement_file:
                            ret_packages += my_requirement_file.readlines()

                for package in ret_packages:
                    package = package.strip()
                    if len(package) == 0:
                        continue
                    if package[0] == '#':
                        continue
                    if len(package.split('==')) >= 2:
                        name, version = package.split('==')
                    elif len(package.split('>=')) >= 2:
                        name, version = package.split('>=')
                    else:
                        name, version = package, ''
                    try:
                        pkg, created = Package.objects.get_or_create(name=name, version=version, project_type=self.repo.project_type)
                        self.packages_from_file.append(pkg)
                    except Exception, e:
                        LOG.exception(e)
                ## FOR
            ## IF
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

    def get_main_url(self):
        urls = self.get_urls()
        for url in urls:
            if not url.startswith('admin/'):
                ret_url = 'http://127.0.0.1:{}/'.format(self.port)
                ret_url = urlparse.urljoin(ret_url, url)
                return ret_url
        return None
    ## DEF

    def sync_server(self, path):
        LOG.info('Syncing server ...')
        command = '{} && {} && unset DJANGO_SETTINGS_MODULE && python manage.py syncdb --noinput'.format(
            utils.to_env(self.base_path), utils.cd(path))
        output = utils.run_command(command)
        if 'Unknown command' in output[2]:
            command = '{} && {} && unset DJANGO_SETTINGS_MODULE && python manage.py migrate --noinput'.format(
            utils.to_env(self.base_path), utils.cd(path))
        return utils.run_command(command)
    ## DEF

    def create_superuser(self, path):
        LOG.info('Creating superuser ...')
        command = '{} && {} && unset DJANGO_SETTINGS_MODULE && {}'.format(
            utils.to_env(self.base_path),
            utils.cd(path),
            """
            echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@test.com', 'admin')" | python manage.py shell
            """)
        return utils.run_command(command)
    ## DEF

    def run_server(self, path, port):
        self.configure_network()
        LOG.info('Running server ...')
        command = '{} && {} && unset DJANGO_SETTINGS_MODULE && python manage.py runserver 0.0.0.0:{}'.format(
            utils.to_env(self.base_path),
            utils.cd(path),
            port)
        return utils.run_command_async(command)
    ## DEF

    def get_runtime(self):
        out = utils.run_command('python --version')[2].split(' ')
        return {
            'executable': out[0],
            'version': out[1]
        }
    ## DEF

    def try_deploy(self, deploy_path, requirement_files):
        LOG.info('Configuring settings ...')
        self.kill_server()
        self.clear_database()
        self.configure_settings()
        self.runtime = self.get_runtime()
        LOG.info(self.runtime)

        self.attempt.database = self.get_database()
        LOG.info('Database: ' + self.attempt.database.name)

        LOG.info('Installing requirements ...')
        self.install_requirements(self.base_path, requirement_files)

        threshold = 20
        last_missing_module_name = ''
        index = -1
        dependencies = []
        for _ in range(threshold):
            output = self.sync_server(deploy_path)
            if output[0] != 0:
                LOG.info(output)
                if self.attempt_info != None:
                    LOG.error("Can not find dependencies!")
                    return
            else:
                LOG.info(output)
                break

            match = re.search('pip install ([a-zA-Z\-_]+)', output[2].strip())
            if match:
                package_name = match.group(1)
                output = utils.pip_install_text(self.base_path, package_name)
                continue
                # LOG.info('pip install output: {}'.format(output))

            split_output = output[2].strip().splitlines()
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
                        LOG.info('pip install {}'.format(candidate_packages[index]))
                        pip_output = utils.pip_install(self.base_path, [candidate_packages[index]], False)
                        LOG.info('pip install output: {}'.format(pip_output))
                    else:
                        LOG.info('No more possible packages!')
                        return ATTEMPT_STATUS_MISSING_DEPENDENCIES
                else:
                    last_missing_module_name = missing_module_name
                    candidate_package_ids = Module.objects.filter(name=missing_module_name).values_list('package_id', flat=True)
                    if not candidate_package_ids:
                        LOG.info('No possible packages!')
                        return ATTEMPT_STATUS_MISSING_DEPENDENCIES
                    
                    candidate_packages = Package.objects.filter(id__in=candidate_package_ids).order_by('-count', '-version', 'name')
                    LOG.info('pip install {}'.format(candidate_packages[0]))
                    pip_output = utils.pip_install(self.base_path, [candidate_packages[0]], False, False)            
                    LOG.info('pip install output: {}'.format(pip_output))
                    try:
                        version = re.search('Successfully installed .*-(.*)', pip_output[1]).group(1)
                        if version and any(package.version == version for package in candidate_packages):
                            for package_index in range(len(candidate_packages)):
                                if candidate_packages[package_index].version == version:
                                    candidate_packages = [candidate_packages[package_index]] + candidate_packages[:package_index] + candidate_packages[package_index + 1:]
                                    break
                        else:
                            latest_package = Package()
                            latest_package.project_type = candidate_packages[0].project_type
                            latest_package.name = candidate_packages[0].name
                            latest_package.version = version
                            latest_package.save()
                            module = Module()
                            module.name = missing_module_name
                            module.package = latest_package
                            module.save()
                            candidate_packages = list([latest_package]) + list(candidate_packages)
                    except Exception, e:
                        LOG.exception(e)
                    dependencies.append((missing_module_name, candidate_packages, 0))
            else:
                return ATTEMPT_STATUS_DATABASE_ERROR
        ## FOR

        for missing_module_name, candidate_packages, index in dependencies:
            self.packages_from_database.append(candidate_packages[index])

        self.create_superuser(deploy_path)

        self.run_server(deploy_path, self.port)

        time.sleep(5)
        
        attemptStatus = self.check_server()

        return attemptStatus
    ## DEF

    def deploy_repo_attempt(self, deploy_path):
        LOG.info(utils.configure_env(self.base_path))

        manage_files = utils.search_file(deploy_path, 'manage.py')
        if not manage_files:
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        manage_paths = [os.path.dirname(manage_file) for manage_file in manage_files]
        base_dir = next(name for name in manage_paths if 'lib/python2.7/site-packages/' not in name)
        manage_path = next(name for name in manage_paths if name.startswith(base_dir))
        LOG.info('manage.py path: {}'.format(manage_path))

        with open(os.path.join(manage_path, 'manage.py'), 'r') as manage_file:
            s = re.search('os.environ.setdefault\("DJANGO_SETTINGS_MODULE", "(.*)"\)', manage_file.read())
            if s:
                setting_path = s.group(1)
            else:
                return ATTEMPT_STATUS_MISSING_REQUIRED_FILES

        setting_path = setting_path.replace('.', '/')
        if os.path.isdir(os.path.join(manage_path, setting_path)):
            setting_path = os.path.join(manage_path, setting_path)
            for setting_file in sorted(os.listdir(setting_path)):
                if os.path.isfile(os.path.join(setting_path, setting_file)):
                    setting_path = os.path.join(setting_path, setting_file)
                    break
            self.setting_path = setting_path
        elif os.path.isfile(os.path.join(manage_path, setting_path + '.py')):
            setting_path = os.path.join(manage_path, setting_path + '.py')
            self.setting_path = setting_path
        else:
            for candidate_setting_files in utils.search_file_regex(deploy_path, '^settings.*\.py$'):
                setting_path = os.path.join(manage_path, setting_path + '.py')
                utils.copy_file(candidate_setting_files, setting_path)
                self.setting_path = setting_path
                break
        if self.setting_path == None:
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        LOG.info('setting.py path: {}'.format(setting_path))

        requirement_files = utils.search_file(deploy_path, 'requirements.txt')
        if requirement_files:
            LOG.info('requirements.txt path: {}'.format(requirement_files))
        
        return self.try_deploy(manage_path, requirement_files)
    ## DEF
    
## CLASS
