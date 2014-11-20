#!/usr/bin/env python
import os
from os.path import join
from utils import run_command, query
from datetime import datetime
import time
import pkgutil
import traceback
from string import Template
import urllib2
import shutil
import logging
import re
import io

repo_deployer_logger = logging.getLogger('repo_deployer')
repo_deployer_logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('repo_deployer.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
repo_deployer_logger.addHandler(fh)
repo_deployer_logger.addHandler(ch)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

import django
django.setup()

from crawler.models import *

def download(repo):
    url = 'https://api.github.com/repos/' + repo.full_name + '/tarball'
#    request = urllib2.Request(url)
#    request.add_header('Authorization', 'token %s' % token)
    response = query(url)
    tar_file = 'tmp.tar'
    tarFile = open(tar_file, 'wb')
    shutil.copyfileobj(response.fp, tarFile)
    tarFile.close()

def tar():
    tar_file = 'tmp.tar'
    #subprocess.call(['tar', '-xf', tar_file])
    #command = "tar -tf " + tar_file + " | grep -o '^[^/]\+' | sort -u"
    command = "tar -xvf " + tar_file + " | grep -o '^[^/]\+' | sort -u"
    directory = ""
    name = run_command(command)
    directory = name.rstrip('\n')
    rm(tar_file)
    return directory

def search_file(directory_name, file_name):
    command = "find " + directory_name + " -type f -wholename '*/" + file_name + "'"
    out = run_command(command)
    out = out.rstrip().splitlines()
    logging.getLogger('repo_deployer').debug('search for ' + file_name + ': ' + str(out))
    logging.getLogger('repo_deployer').debug('search for ' + file_name + ': ' + str(out))
    return out

def append_settings(setting):
    settings = """
SECRET_KEY = 'abcdefghijklmnopqrstuvwxyz'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db_webcrawler',
    }
}
    """
    with open(setting, "a") as setting_file:
        setting_file.write(settings)
    logging.getLogger('repo_deployer').debug('appended to settings.py: ' + str(settings))
    logging.getLogger('basic_logger').debug('appended to settings.py: ' + str(settings))

def vagrant_pip_freeze():
    out = run_command("vagrant ssh -c 'pip freeze'")
    out = out.rstrip().splitlines()
    out = [line for line in out if not ' ' in line and '==' in line]
    return set(out)

def vagrant_pip_clear():
    out = run_command("vagrant ssh -c 'sudo rm -rf /home/vagrant/pip/build/ /home/vagrant/.local/'")
    return out

def to_vm_file(file_name):
    return join('/vagrant', file_name)


def vagrant_pip_rm_build():
    out = run_command("vagrant ssh -c 'sudo rm -rf /home/vagrant/pip/build/ '")
    return out

def vagrant_pip_install(name, is_file):
    command_t = Template("vagrant ssh -c 'pip ${proxy} install --user --build /home/vagrant/pip/build ")
    proxy = os.environ.get('http_proxy')
    if proxy:
        command = command_t.substitute(proxy="--proxy " + proxy)
    else:
        command = command_t.substitute(proxy='')
    if is_file:
        vm_name = to_vm_file(name)
        command = command + "-r " + vm_name
    else:
        command = command + name.name + "==" + name.version
    command = command + "'"
    out = run_command(command)
    vagrant_pip_rm_build()
    return out

def install_requirements(requirement_files, repo, attempt):
    if requirement_files:
        vagrant_pip_clear()
        if repo.repo_type.name == 'Django':
            old_packages = vagrant_pip_freeze()
            logging.getLogger('repo_deployer').debug('pip freeze output: ' + str(old_packages))
            logging.getLogger('basic_logger').debug('pip freeze output: ' + str(old_packages))
            for requirement_file in requirement_files:
                out = vagrant_pip_install(requirement_file, True)
                logging.getLogger('repo_deployer').debug('installed requirements output: ' + out)
                logging.getLogger('basic_logger').debug('installed requirements output: ' + out)
            new_packages = vagrant_pip_freeze()
            logging.getLogger('repo_deployer').debug('pip freeze output: ' + str(new_packages))
            logging.getLogger('basic_logger').debug('pip freeze output: ' + str(new_packages))
            diff_packages = new_packages - old_packages
            logging.getLogger('repo_deployer').debug('installed packages: ' + str(diff_packages))
            logging.getLogger('basic_logger').debug('installed packages: ' + str(diff_packages))
            for package in diff_packages:
                logging.getLogger('repo_deployer').debug('recording package: ' + package)
                logging.getLogger('basic_logger').debug('installed packages: ' + package)
                name, version = package.split('==')
                obj, created = Package.objects.get_or_create(name=name, version=version, package_type=Type(name='Django'))
                if created:
                    logging.getLogger('repo_deployer').debug('a new package: ' + package)
                    logging.getLogger('basic_logger').debug('a new package: ' + package)
                else:
                    logging.getLogger('repo_deployer').debug('a old package: ' + package)
                    logging.getLogger('basic_logger').debug('a old package: ' + package)

                dep = Dependency()
                dep.attempt = attempt
                dep.package = obj
                dep.source = Source(name='File')
                dep.save()
                obj.count = obj.count + 1
                obj.save()
        elif repo.repo_type.name == "Ruby on Rails":
#TODO: implement ruby on rails
            pass
            
def vagrant_syncdb(manage_file, repo):
    vm_manage_file = to_vm_file(manage_file)
    command = "vagrant ssh -c 'python " + vm_manage_file + " syncdb --noinput'"
    out = run_command(command) 
    return out

def vagrant_runserver(manage_file):
    vm_manage_file = to_vm_file(manage_file)
    command = 'vagrant ssh -c ' + "'python " + vm_manage_file + " runserver > /vagrant/log 2>&1 & sleep 10'"
    run_command(command)
    with open ("log", "r") as myfile:
        out = myfile.read()
    return out

def save_attempt(attempt, result, log_capture_string):
    attempt.result = Result(name=result)
    attempt.log = log_capture_string.getvalue()
    attempt.save()
    log_capture_string.close()
#    for pkg in pkgs_from_f:
#        Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=Source(name='File'))
#    for pkg in pkgs_from_db:
#        Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=Source(name='Database'))

def deploy(manage_file, setting_file, requirement_files, repo, attempt, log_capture_string):
    append_settings(setting_file)

    install_requirements(requirement_files, repo, attempt)

    threshold = 100
    last_missing_module_name = ''
    index = 0
    #candidate_packages = []
    packages_from_database = []
    for time in range(threshold):
        logging.getLogger('repo_deployer').debug('deploying try #' + str(time))
        logging.getLogger('basic_logger').debug('deploying try #' + str(time))
        out = vagrant_syncdb(manage_file, repo)
        logging.getLogger('repo_deployer').debug('syncdb output: ' + out)
        logging.getLogger('basic_logger').debug('syncdb output: ' + out)
        out = out.strip()
        out = out.splitlines()
        if out and out[-1].strip().startswith('ImportError'):
            line = out[-1].strip()
            match = re.search('(?<=No module named )\S+', line)
            if match:
                missing_module_name = match.group(0)
                logging.getLogger('repo_deployer').debug('missing module name: ' + missing_module_name)
                logging.getLogger('basic_logger').debug('missing module name: ' + missing_module_name)
                logging.getLogger('repo_deployer').debug('last missing module name: ' + last_missing_module_name)
                logging.getLogger('basic_logger').debug('last missing module name: ' + last_missing_module_name)

                if missing_module_name == last_missing_module_name:
                    index = index + 1
                    if index == len(candidate_packages):
                        save_attempt(attempt, "Missing Dependencies", log_capture_string)
                        for pkg in packages_from_database:
                            dep = Dependency()
                            dep.attempt = attempt
                            dep.package = pkg
                            dep.source = Source(name='Database')
                            dep.save()
                        return
                    out = vagrant_pip_install(candidate_packages[index], False)
                    logging.getLogger('repo_deployer').debug('install requirements output: ' + str(out))
                    logging.getLogger('basic_logger').debug('install requirements output: ' + str(out))
                else:
                    if last_missing_module_name != '':
                        packages_from_database.append(candidate_packages[index])
#                    candidate_package_ids = Module.objects.filter(name__endswith=missing_module_name).extra(select={'length':'Length(name)'}).order_by('length', '-package__count', 'package__name', '-package__version').values_list('package_id', flat=True)
                    candidate_package_ids = Module.objects.filter(name=missing_module_name).values_list('package_id', flat=True)
                    if not candidate_package_ids:
                        save_attempt(attempt, "Missing Dependencies", log_capture_string)
                        for pkg in packages_from_database:
                            dep = Dependency()
                            dep.attempt = attempt
                            dep.package = pkg
                            dep.source = Source(name='Database')
                            dep.save()
                        return
                    last_missing_module_name = missing_module_name
                    #packages_from_file = [pkg for pkg in packages_from_file if pkg.id not in pckage_ids]
                    candidate_packages = Package.objects.filter(id__in=candidate_package_ids).order_by('-count', 'name', '-version')
                    
                    #candidate_packages = []
                    #for candidate_package_id in candidate_package_ids:
                    #    pkg = Package.objects.get(id=candidate_package_id)
                    #    candidate_packages.append(pkg)
                    for pkg in candidate_packages:
                        logging.getLogger('repo_deployer').debug('candidate package: ' + pkg.name + '==' + pkg.version)
                        logging.getLogger('basic_logger').debug('candidate package: ' + pkg.name + '==' + pkg.version)
                    index = 0
                    vagrant_pip_install(candidate_packages[0], False)
                    logging.getLogger('repo_deployer').debug('install requirements output: ' + str(out))
                    logging.getLogger('basic_logger').debug('install requirements output: ' + str(out))
            else:
                save_attempt(attempt, "Missing Dependencies", log_capture_string)
                for pkg in packages_from_database:
                    dep = Dependency()
                    dep.attempt = attempt
                    dep.package = pkg
                    dep.source = Source(name='Database')
                    dep.save()
                return
        else:
            if last_missing_module_name != '':
                packages_from_database.append(candidate_packages[index])
            break
    for pkg in packages_from_database:
        dep = Dependency()
        dep.attempt = attempt
        dep.package = pkg
        dep.source = Source(name='Database')
        dep.save()
    out = vagrant_runserver(manage_file)
    logging.getLogger('repo_deployer').debug('runserver output: ' + out)
    logging.getLogger('basic_logger').debug('runserver output: ' + out)
    out = out.strip().splitlines()
    if out:
        line = out[-1].strip()
        if line.startswith('ImportError'):
            save_attempt(attempt, "Missing Dependencies", log_capture_string)
        else:
            save_attempt(attempt, "Running Error", log_capture_string)
    else:
        save_attempt(attempt, "Success", log_capture_string)

def rm(file_name):
    command = 'rm ' + file_name
    run_command(command)

def rm_dir(directory_name):
    command = 'rm -rf ' + directory_name
    run_command(command)

if __name__ == '__main__':
    download_url_template = Template('https://api.github.com/repos/${full_name}/tarball')
    vagrant_pip_clear()
    logger = logging.getLogger('basic_logger')
    logger.setLevel(logging.DEBUG)
    while True:
        repos = Repository.objects.exclude(pk__in=Attempt.objects.values_list('repo', flat=True))
        for repo in repos:
            log_capture_string = io.BytesIO()
            ch = logging.StreamHandler(log_capture_string)
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(formatter)
            logger.addHandler(ch)
            logging.getLogger('repo_deployer').debug('deploying repo: ' + repo.full_name)
            logging.getLogger('basic_logger').debug('deploying repo: ' + repo.full_name)
            attempt = Attempt()
            attempt.repo = repo
            if repo.last_attempt:
                attempt.local_id = repo.last_attempt.local_id + 1
            else:
                attempt.local_id = 1
            attempt.result = Result(name="Deploying")
            attempt.time = datetime.now()
            attempt.log = ''
            attempt.save()

            repo.last_attempt = attempt
            repo.save()

            download_url = download_url_template.substitute(full_name=repo.full_name)
            logging.getLogger('repo_deployer').debug('Downloading repo: ' + repo.full_name)
            logging.getLogger('basic_logger').debug('Downloading repo: ' + repo.full_name)
            try:
                 download(repo)
            except:
                logging.getLogger('repo_deployer').debug(traceback.print_exc())
                logging.getLogger('basic_logger').debug(traceback.print_exc())
                save_attempt(attempt, "Download Error")
                continue
            directory_name = tar()
            logging.getLogger('repo_deployer').debug('directory_name = ' + directory_name)
            logging.getLogger('basic_logger').debug('directory_name = ' + directory_name)

            setup_files = search_file(directory_name, 'setup.py')
            if len(setup_files):
                save_attempt(attempt, "Not an Application", log_capture_string)
                rm_dir(directory_name)
                continue

            manage_files = search_file(directory_name, 'manage.py')
            if not len(manage_files):
                save_attempt(attempt, "Missing Required Files", log_capture_string)
                rm_dir(directory_name)
                continue
            elif len(manage_files) != 1:
                save_attempt(attempt, "Duplicate Required Files", log_capture_string)
                rm_dir(directory_name)
                continue
            
            setting_files = search_file(directory_name, 'settings.py')
            if not len(setting_files):
                save_attempt(attempt, "Missing Required Files", log_capture_string)
                rm_dir(directory_name)
                continue
            elif len(setting_files) != 1:
                save_attempt(attempt, "Duplicate Required Files", log_capture_string)
                rm_dir(directory_name)
                continue

            requirement_files = search_file(directory_name, 'requirements.txt')

            deploy(manage_files[0], setting_files[0], requirement_files, repo, attempt, log_capture_string)
            vagrant_pip_clear()
            rm_dir(directory_name)
