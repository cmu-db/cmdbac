#!/usr/bin/env python
import os
import sys
from os.path import join
import datetime
import time
import pkgutil
import traceback
from string import Template
import urllib2
import shutil
import logging
import re
import io
import json
from bs4 import BeautifulSoup
import socket

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

# import * from convinient
from crawler.models import *
from utils import *

def save_attempt(attempt, result, log_str, pkgs_from_f=[], pkgs_from_db=[]):
    attempt.result = Result(name=result)
    #attempt.log = log_str.getvalue()
    attempt.log = log_str
    
    attempt.duration = (datetime.datetime.now() - attempt.start_time).total_seconds()
    attempt.save()
    #log_str.close()
    for pkg in pkgs_from_f:
        dep = Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=Source(name='File'))
        pkg.count = pkg.count + 1
        pkg.save()
    for pkg in pkgs_from_db:
        Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=Source(name='Database'))

def try_deploy_django(manage_file, setting_file, requirement_files, attempt, log_str):
    rewrite_settings(setting_file, 'Django')
    log_str = log(log_str, 'settings appended')
    kill_server('Django')

    packages = install_requirements(requirement_files, "Django")
    installed_requirements = []
    for package in packages:
        name, version = package.split('==')
        pkg, created = Package.objects.get_or_create(name=name, version=version, package_type=Type(name='Django'))
        installed_requirements.append(pkg)
    
    log_str = log(log_str, 'installed_requirements: ' + str(installed_requirements))

    threshold = 10
    last_missing_module_name = ''
    index = 0
    #candidate_packages = []
    packages_from_database = []
    for tmp in range(threshold):
        out = vagrant_syncdb(manage_file, "Django")
        log_str = log(log_str, 'syncdb output: ' + out) 
        out = out.strip()
        out = out.splitlines()
        if out and out[-1].strip().startswith('ImportError'):
            line = out[-1].strip()
            match = re.search('(?<=No module named )\S+', line)
            if match:
                missing_module_name = match.group(0)
                log_str = log(log_str, 'missing module: ' + missing_module_name) 
                if missing_module_name == last_missing_module_name:
                    index = index + 1
                    if index == len(candidate_packages):
                        log_str = log(log_str, 'no more possible package')
                        save_attempt(attempt, "Missing Dependencies", log_str, installed_requirements, packages_from_database)
                        return
                    out = vagrant_pip_install([candidate_packages[index]], False)
                    log_str = log(log_str, 'pip install output: ' + out)
                else:
                    if last_missing_module_name != '':
                        packages_from_database.append(candidate_packages[index])
                    candidate_package_ids = Module.objects.filter(name=missing_module_name).values_list('package_id', flat=True)
                    if not candidate_package_ids:
                        log_str = log(log_str, 'no possible package')
                        save_attempt(attempt, "Missing Dependencies", log_str, installed_requirements, packages_from_database)
                        return
                    last_missing_module_name = missing_module_name
                    #packages_from_file = [pkg for pkg in packages_from_file if pkg.id not in pckage_ids]
                    candidate_packages = Package.objects.filter(id__in=candidate_package_ids).order_by('-count', 'name', '-version')
                    log_str = log(log_str, 'candidate packages: ' + str(candidate_packages))
                    index = 0
                    out = vagrant_pip_install([candidate_packages[0]], False)
                    log_str = log(log_str, 'pip install output: ' + out)
            else:
                save_attempt(attempt, "Missing Dependencies", log_str, installed_requirements, packages_from_database)
                return
        else:
            if last_missing_module_name != '':
                packages_from_database.append(candidate_packages[index])
            break
    out = vagrant_runserver(manage_file, 'Django')
    
    print out
    log_str = log(log_str, out)
    time.sleep(10)
    urls = get_urls(os.path.dirname(setting_file), 'Django')
    print urls
    urls = list(set([re.sub(r'[\^\$]', '', url) for url in urls if '?' not in url]))
    #urls = list(set([re.sub(r'\([^)]*\)', '', url) for url in urls if '?' not in url]))
    urls = sorted(urls, key=len)
    print urls
    log_str = log(log_str, out)
    for url in urls:
        out = check_server(url, 'Django')
        print out
        log_str = log(log_str, out)
        if "200 OK" in out:
            save_attempt(attempt, "Success", log_str, installed_requirements, packages_from_database)
            kill_server('Django')
            return
    save_attempt(attempt, "Running Error", log_str, installed_requirements, packages_from_database)
    kill_server('Django')
    
#    log_str = log(log_str, 'runserver output: ' + out)
#    out = out.strip().splitlines()
#    if out:
#        line = out[-1].strip()
#        if line.startswith('ImportError'):
#            log_str = log(log_str, 'import error')
#            save_attempt(attempt, "Missing Dependencies", log_str, installed_requirements, packages_from_database)
#        else:
#            log_str = log(log_str, 'running error')
#            save_attempt(attempt, "Running Error", log_str, installed_requirements, packages_from_database)
#    else:
#        log_str = log(log_str, 'success')
#        save_attempt(attempt, "Success", log_str, installed_requirements, packages_from_database)


#    vagrant_runserver(manage_file)
#    p_id = vagrant_netstat()
#    if p_id:
#        save_attempt(attempt, "Success", log_str, installed_requirements, packages_from_database)
#        vagrant_kill(p_id)
#    else:
#        with open ("log", "r") as myfile:
#            out = myfile.read()
#        out = out.strip().splitlines()
#        if out:
#            line = out[-1].strip()
#            if line.startswith('ImportError'):
#                save_attempt(attempt, "Missing Dependencies", log_str, installed_requirements, packages_from_database)
#            else:
#                save_attempt(attempt, "Running Error", log_str, installed_requirements, packages_from_database)
#        else:
#            save_attempt(attempt, "Unknown", log_str, installed_requirements, packages_from_database)

def rm(file_name):
    os.remove(file_name)
    #command = 'rm ' + file_name
    #run_command(command)

def get_database(settings_file, type_name):
    with open(settings_file, 'r') as infile:
        if type_name == "Django":
            for line in infile:
                p = re.search('django.db.backends.(.*)', line);
                if p:
                    db = p.group(1)
                    if db.startswith('postgresql_psycopg2'):
                        return Database(name='PostgreSQL')
                    elif db.startswith('mysql'):
                        return Database(name='MySQL')
                    elif db.startswith('sqlite3'):
                        return Database(name='SQLite3')
                    elif db.startswith('oracle'):
                        return Database(name='Oracle')
            for line in infile:
                p = re.search("adapter\s*:\s*(.*)", line);
                if p:
                    db = p.group(1)
                    if 'sqlite' in db:
                        return Database(name='SQLite3')
                    elif 'mysql' in db:
                        return Database(name='MySQL')
                    elif 'postgresql' in db:
                        return Database(name='PostgreSQL')
                    elif 'oracle' in db:
                        return Database(name='Oracle')
    return Database(name='Other')

def log(string, log):
    return string + log.decode('utf-8') + '\n'

def try_deploy_ror(path, attempt, log_str):
    rewrite_settings(path, 'Ruby on Rails')
    print 'try deploy ror'
    kill_server('Ruby on Rails')
    out = install_requirements(path, 'Ruby on Rails')
    print out
    log_str = log(log_str, out)
    if not "Your bundle is complete!" in out:
        save_attempt(attempt, "Missing Dependencies", log_str)
        return

    out = vagrant_syncdb(path, "Ruby on Rails")
    print out
    log_str = log(log_str, out)
    if "rake aborted!" in out:
        save_attempt(attempt, "Running Error", log_str)
        return
    out = vagrant_runserver(path, 'Ruby on Rails')
    print out
    log_str = log(log_str, out)
    time.sleep(10)
    urls = get_urls(path, 'Ruby on Rails')
    print urls
    urls = [re.sub(r'\([^)]*\)', '', url) for url in urls]
    urls = list(set([url for url in urls if ':' not in url]))
    urls = sorted(urls, key=len)
    print urls
    log_str = log(log_str, str(urls))
    log_str = log(log_str, str(urls))
    for url in urls:
        out = check_server(url, 'Ruby on Rails')
        print out
        log_str = log(log_str, out)
        if "200 OK" in out:
            save_attempt(attempt, "Success", log_str)
            kill_server('Ruby on Rails')
            return
    save_attempt(attempt, "Running Error", log_str)
    kill_server('Ruby on Rails')

ZIP = "tmp.zip"
DIR = "tmp_dir"

def deploy_repo(repo):
    log_str = ''
    log_str = log(log_str, 'deploying repo: ' + repo.full_name)
    attempt = Attempt()
    attempt.repo = repo
    attempt.result = Result(name="Deploying")
    attempt.start_time = datetime.datetime.now()
    attempt.hostname = socket.gethostname()
    attempt.save()
    repo.latest_attempt = attempt
    repo.attempts_count = repo.attempts_count + 1
    repo.save()
    try:
        sha = get_latest_sha(repo)
    except:
        save_attempt(attempt, "Download Error", log_str)
        return
    attempt.sha = sha

    log_str = log(log_str, 'Downloading repo: ' + repo.full_name + attempt.sha)
    try:
         download(attempt, ZIP)
    except:
        print traceback.print_exc()
        save_attempt(attempt, "Download Error", log_str)
        return
    remake_dir(DIR)
    unzip(ZIP, DIR)
    print DIR
    log_str = log(log_str, 'DIR = ' + DIR)
    print 'type'
    print repo.repo_type.name
    if repo.repo_type.name == "Django":
        vagrant_pip_clear()
        #log_str = io.BytesIO()
        #ch = logging.StreamHandler(log_str)
        #ch.setLevel(logging.DEBUG)
        #ch.setFormatter(formatter)
        #logger.addHandler(ch)

        setup_files = search_file(DIR, 'setup.py')
        log_str = log(log_str, 'setup.py: ' + str(setup_files))
        if len(setup_files):
            save_attempt(attempt, "Not an Application", log_str)
            return

        setting_files = search_file(DIR, 'settings.py')
        log_str = log(log_str, 'settings.py: ' + str(setting_files))
        if not len(setting_files):
            save_attempt(attempt, "Missing Required Files", log_str)
            return
#                elif len(setting_files) != 1:
#                    save_attempt(attempt, "Duplicate Required Files", log_str)
#                    continue
        
                
        manage_files = search_file(DIR, 'manage.py')
        log_str = log(log_str, 'manage.py: ' + str(manage_files))
        if not len(manage_files):
            save_attempt(attempt, "Missing Required Files", log_str)
            return
#                elif len(manage_files) != 1:
#                    save_attempt(attempt, "Duplicate Required Files", log_str)
#                    continue

        requirement_files = search_file(DIR, 'requirements.txt')
        log_str = log(log_str, 'requirements.txt' + str(requirement_files))

        
        manage_paths = [os.path.dirname(manage_file) for manage_file in manage_files]
        print manage_paths
        setting_paths = [os.path.dirname(os.path.dirname(setting_file)) for setting_file in setting_files]
        print setting_paths
        base_dirs = set.intersection(set(manage_paths), set(setting_paths))
        if not base_dirs:
            print 'can not find base directory'
            save_attempt(attempt, "Missing Required Files", log_str)
            return
        base_dir = next(iter(base_dirs))
        print 'base_dir: ' + base_dir
        manage_file = next(name for name in manage_files if name.startswith(base_dir))
        setting_file = next(name for name in setting_files if name.startswith(base_dir))
        attempt.database = get_database(setting_file, "Django")
        print 'Database: ' + attempt.database.name
        log_str = log(log_str, 'database: ' + attempt.database.name)
        attempt.base_dir = base_dir.split('/', 1)[1]
        print 'base_dir: ' + attempt.base_dir
        attempt.setting_dir = os.path.basename(os.path.dirname(setting_file))
        print 'setting_dir: ' + attempt.setting_dir
        try_deploy_django(manage_file, setting_file, requirement_files, attempt, log_str)
    elif repo.repo_type.name == "Ruby on Rails":
        print 'directory: ' + DIR

        rakefiles = search_file(DIR, 'Rakefile')
        if not rakefiles:
            print 'no rakefile found'
            save_attempt(attempt, "Missing Required Files", log_str)
            return
        rakefile_paths = [os.path.dirname(rakefile) for rakefile in rakefiles]
        #print 'rakefile_paths: ' + str(rakefile_paths)
        #elif len(rakefiles) != 1:
        #    print 'multiple rakefiles found'
        #    save_attempt(attempt, "Duplicate Required Files", log_str)
        #    continue
        print 'Finding database'
        gemfiles = search_file(DIR, 'Gemfile')
        if not gemfiles:
            print 'no gemfile'
            save_attempt(attempt, "Missing Required Files", log_str)
            return
        gemfile_paths = [os.path.dirname(gemfile) for gemfile in gemfiles]
        #print 'gemfile_paths: ' + str(gemfile_paths)
        db_files = search_file(DIR, 'database.yml')
        if not db_files:
            print 'not use database'
            save_attempt(attempt, "Missing Required Files", log_str)
            return

        print 'using database'
        db_file_paths = [os.path.dirname(os.path.dirname(db_file)) for db_file in db_files if os.path.basename(os.path.normpath(os.path.dirname(db_file))) == "config"]
        #print 'db_file_paths: ' + str(db_file_paths)
        base_dirs = set.intersection(set(rakefile_paths), set(gemfile_paths), set(db_file_paths))
        if not base_dirs:
            print 'can not find base directory'
            save_attempt(attempt, "Missing Required Files", log_str)
            return
        base_dir = next(iter(base_dirs))
        attempt.base_dir = base_dir.split('/', 1)[1]

        print 'base_dir: ' + base_dir

        attempt.database = get_database(os.path.join(base_dir, 'config/database.yml'), "Ruby on Rails")
        print attempt.database.name
        log_str = log(log_str, 'database: ' + attempt.database.name)
        attempt.save()
        try_deploy_ror(base_dir, attempt, log_str)

def main():
    logger = logging.getLogger('basic_logger')
    logger.setLevel(logging.DEBUG)
    string = None
    if len(sys.argv) > 1:
        string = sys.argv[1]
    if string:
        if string == 'django':
            string = 'Django'
        elif string == 'ror':
            string = 'Ruby on Rails'
        else:
            try:
                repo = Repository.objects.get(full_name=sys.argv[1])
            except:
                print 'can not find the repository ' + sys.argv[1]
            deploy_repo(repo)
            return
            
    while True:
        repos = Repository.objects.exclude(pk__in=Attempt.objects.values_list('repo', flat=True))
# add the line if we what to get a specific type of repositories
        if string:
            repos = repos.filter(repo_type__name=string)
        for repo in repos:
            deploy_repo(repo)

if __name__ == '__main__':
    main()
