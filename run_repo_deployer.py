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

logging.basicConfig(filename='repo_deployer.log',level=logging.DEBUG)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

import django
django.setup()

from crawler.models import *

#def check_files(directory_name, attempt):

log = ''

def log_run_command(command):
    global log
    out = run_command(command)
    log = log + out
    return out


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
    name = log_run_command(command)
    directory = name.rstrip('\n')
    rm(tar_file)
    return directory

def search_file(directory_name, file_name):
    command = "find " + directory_name + " -type f -wholename '*/" + file_name + "'"
    out = log_run_command(command)
    out = out.rstrip().splitlines()
    print out
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

def vagrant_pip_freeze():
    out = log_run_command("vagrant ssh -c 'pip freeze'")
    out = out.rstrip().splitlines()
    out = [line for line in out if not ' ' in line and '==' in line]
    return set(out)

def vagrant_pip_clear():
    log_run_command("vagrant ssh -c 'sudo rm -rf /home/vagrant/pip/build/ /home/vagrant/.local/'")

def to_vm_file(file_name):
    return join('/vagrant', file_name)


def vagrant_pip_rm_build():
    log_run_command("vagrant ssh -c 'sudo rm -rf /home/vagrant/pip/build/ '")

def vagrant_pip_install(name, is_file):
    command = "vagrant ssh -c 'pip --proxy http://proxy.pdl.cmu.edu:8080 install --user --build /home/vagrant/pip/build " 
    if is_file:
        vm_name = to_vm_file(name)
        command = command + "-r " + vm_name
    else:
        command = command + name.name + "==" + name.version
    command = command + "'"
    log_run_command(command)
    vagrant_pip_rm_build()

def install_requirements(requirement_files, repo, attempt):
#    vm_requirement_files = [join("/vagrant", requirement_file) for requirement_file in requirement_files]
#    print vm_requirement_files
    if requirement_files:
        packages = []
        vagrant_pip_clear()
        if repo.repo_type.repo_type == 'Django':
            old_packages = vagrant_pip_freeze()
            for requirement_file in requirement_files:
                vagrant_pip_install(requirement_file, True)
            new_packages = vagrant_pip_freeze()
            diff_packages = new_packages - old_packages
            for package in diff_packages:
                name, version = package.split('==')
                obj, created = Package.objects.get_or_create(name=name, version=version)
                if created:
                    print "find new package from requirement file: " + name + '==' + version
                packages.append(obj)
                #dep, created = Dependency.objects.get_or_create(attempt=attempt, package=obj, source=Source(source='File'))
            return packages
        else:
            return []
    else:
        return []
            
def vagrant_syncdb(manage_file, repo):
    vm_manage_file = to_vm_file(manage_file)
    command = "vagrant ssh -c 'python " + vm_manage_file + " syncdb --noinput'"
    out = log_run_command(command) 
    return out

def vagrant_runserver(manage_file):
    vm_manage_file = to_vm_file(manage_file)
    command = 'vagrant ssh -c ' + "'python " + vm_manage_file + " runserver > /vagrant/log 2>&1 & sleep 10'"
    log_run_command(command)
    with open ("log", "r") as myfile:
        out = myfile.read()
    return out

def save_attempt(attempt, result, log=log, pkgs_from_f=[], pkgs_from_db=[]):
    attempt.result = Result(result=result)
    attempt.log = log
    attempt.save()
    for pkg in pkgs_from_f:
        Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=Source(source='File'))
    for pkg in pkgs_from_db:
        Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=Source(source='Database'))

def deploy(manage_file, setting_file, requirement_files, repo, attempt):
    append_settings(setting_file)

    packages_from_file = install_requirements(requirement_files, repo, attempt)
    print 'installed packages: '
    for pkg in packages_from_file:
        print pkg.name + '==' + pkg.version

    threshold = 100
    last_missing_module_name = ''
    index = 0
    candidate_packages = []
    packages_from_database = []
    for time in range(threshold):
        print 'try #' + str(time)
        #package_from_db, success = vagrant_syncdb(manage_file, repo)
        out = vagrant_syncdb(manage_file, repo)
        out = out.rstrip()
        print 'stripped output: '
        print out
        out = out.splitlines()
        if out and out[-1].strip().startswith('ImportError'):
            line = out[-1].strip()
            print 'line: ' + line
            missing_module_name = out[-2].strip().split()[1]
            print 'missing module name: ' + missing_module_name
            print 'last missing module name: ' + last_missing_module_name
            if missing_module_name == last_missing_module_name:
                index = index + 1
                print 'index=' + str(index)
                if index == len(candidate_packages):
                    save_attempt(attempt, "Missing Dependencies", log, packages_from_file, packages_from_database)
                
                else:
                    vagrant_pip_install(candidate_packages[index], False)
            else:
                if last_missing_module_name != '':
                    packages_from_database.append(candidate_packages[index])
                candidate_package_ids = Module.objects.filter(name=missing_module_name).values_list('package_id', flat=True)
                if not candidate_package_ids:
                    save_attempt(attempt, "Missing Dependencies", log, packages_from_file, packages_from_database)
                else:
                    last_missing_module_name = missing_module_name
                    #packages_from_file = [pkg for pkg in packages_from_file if pkg.id not in pckage_ids]
                    candidate_packages = Package.objects.filter(id__in=candidate_package_ids).order_by('name', '-version')
                    print 'candidate package size: ' + str(len(candidate_packages))
                    print candidate_packages
                    index = 0
                    #for candidate_package in candidate_packages:
                    vagrant_pip_install(candidate_packages[0], False)

        else:
            if last_missing_module_name != '':
                packages_from_database.append(candidate_packages[index])

            break

    out = vagrant_runserver(manage_file)
    out = out.rstrip()
    print 'runserver output: ' + out
    if out:
        out = out.splitlines()
        line = out[-1].strip()
        if line.startswith('ImportError'):
            save_attempt(attempt, "Missing Dependencies", log, packages_from_file, packages_from_database)
        else:
            save_attempt(attempt, "Running Error", log, packages_from_file, packages_from_database)

    else:
        save_attempt(attempt, "Success", log, packages_from_file, packages_from_database)



#    result , log = runserver(manage_file, repo)

def rm(file_name):
    command = 'rm ' + file_name
    log_run_command(command)

def rm_dir(directory_name):
    command = 'rm -rf ' + directory_name
    log_run_command(command)



if __name__ == '__main__':
    download_url_template = Template('https://api.github.com/repos/${full_name}/tarball')
    vagrant_pip_clear()
    while True:
        repos = Repository.objects.exclude(pk__in=Attempt.objects.values_list('repo', flat=True))
        for repo in repos:
            log = ''
            print 'deploying repo: ' + repo.full_name
            log = log + 'deploying repo: ' + repo.full_name + '\n'
            attempt = Attempt()
            attempt.repo = repo
            attempt.time= datetime.now()
            save_attempt(attempt, "Deploying")
            download_url = download_url_template.substitute(full_name=repo.full_name)
            try:
                 download(repo)
            except:
                save_attempt(attempt, "Download Error", traceback.print_exc())
                continue
            directory_name = tar()
            #attempt, success = check_files(directory_name, attempt)
            setup_files = search_file(directory_name, 'setup.py')
            print len(setup_files)
            if len(setup_files):
                save_attempt(attempt, "Not an Application", str(setup_files))
                rm_dir(directory_name)
                continue

            manage_files = search_file(directory_name, 'manage.py')
            print type(manage_files)
            print len(manage_files)
            if not len(manage_files):
                save_attempt(attempt, "Missing Required Files", "can't find manage.py")
                rm_dir(directory_name)
                continue
            elif len(manage_files) != 1:
                save_attempt(attempt, "Duplicate Required Files", "find more than one manage.py")
                rm_dir(directory_name)
                continue
            
            setting_files = search_file(directory_name, 'settings.py')
            print len(setting_files)
            if not len(setting_files):
                save_attempt(attempt, "Missing Required Files", "can't find settings.py")
                rm_dir(directory_name)
                continue
            elif len(setting_files) != 1:
                save_attempt(attempt, "Duplicate Required Files", "find more than one settings.py")
                rm_dir(directory_name)
                continue

            requirement_files = search_file(directory_name, 'requirements.txt')
            print len(requirement_files)

            #result, log, pkg_from_file, pkg_from_db = deploy(manage_files[0], setting_files[0], requirement_files, repo)
            deploy(manage_files[0], setting_files[0], requirement_files, repo, attempt)
            vagrant_pip_clear()
            rm_dir(directory_name)
