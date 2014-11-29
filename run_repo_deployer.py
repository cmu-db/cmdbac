#!/usr/bin/env python
import os
from os.path import join
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
    
    attempt.save()
    #log_str.close()
    for pkg in pkgs_from_f:
        Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=Source(name='File'))
    for pkg in pkgs_from_db:
        Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=Source(name='Database'))

def try_deploy(manage_file, setting_file, requirement_files, attempt, log_str):
    rewrite_settings(setting_file, 'Django')
    log_str = log(log_str, 'settings appended')

    installed_requirements = install_requirements(requirement_files)
    log_str = log(log_str, 'installed_requirements: ' + str(installed_requirements))

    threshold = 100
    last_missing_module_name = ''
    index = 0
    #candidate_packages = []
    packages_from_database = []
    for time in range(threshold):
        out = vagrant_syncdb(manage_file)
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
                    out = vagrant_pip_install(candidate_packages[index], False)
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
                    out = vagrant_pip_install(candidate_packages[0], False)
                    log_str = log(log_str, 'pip install output: ' + out)
            else:
                save_attempt(attempt, "Missing Dependencies", log_str, installed_requirements, packages_from_database)
                return
        else:
            if last_missing_module_name != '':
                packages_from_database.append(candidate_packages[index])
            break
    out = vagrant_runserver(manage_file)
    log_str = log(log_str, 'runserver output: ' + out)
    out = out.strip().splitlines()
    if out:
        line = out[-1].strip()
        if line.startswith('ImportError'):
            log_str = log(log_str, 'import error')
            save_attempt(attempt, "Missing Dependencies", log_str, installed_requirements, packages_from_database)
        else:
            log_str = log(log_str, 'running error')
            save_attempt(attempt, "Running Error", log_str, installed_requirements, packages_from_database)
    else:
        log_str = log(log_str, 'success')
        save_attempt(attempt, "Success", log_str, installed_requirements, packages_from_database)
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

def get_database(settings_file):
    with open(settings_file, 'r') as infile:
        if settings_file.endswith('settings.py'):
            for line in infile:
                p = re.match('django.db.backends.(.*)', line);
                if p:
                    db = p.group(1)
                    if db.startswith('postgresql_psycopg2'):
                        return Database(name='PostgreSQL')
                    elif db.startswith('mysql'):
                        return Database(name='MySQL')
                    elif db.starswith(sqlite3):
                        return Database(name='SQLite3')
                    elif db.startswith(oracle):
                        return Database(name='Oracle')
        elif settings_file.endswith('database.yml'):
            for line in infile:
                p = re.match("adapter(\s*):(\s*)(.*)", line);
                if p:
                    db = p.group(3)
                    if 'sqlite' in db:
                        return Database(name='SQLite3')
                    elif 'mysql' in db:
                        return Database(name='MySQL')
                    elif 'postgresql' in db:
                        return Database(name='PostgreSQL')
                    elif 'oracle' in db:
                        return Database(name='Orable')
    return Database(name='Other')

def log(string, log):
    return string + log + '\n'

def try_deploy_ror(path, attempt, log_str):
    print 'try deploy ror'
    out = vagrant_bundle_install(path)
    print out
    log_str = log(log_str, out)
    out = vagrant_rake_db_create(path)
    print out
    log_str = log(log_str, out)
    out = vagrant_rails_server(path)
    print out
    log_str = log(log_str, out)
    save_attempt(attempt, "Success", log_str)
    
if __name__ == '__main__':
    mk_tmp_dir()
    logger = logging.getLogger('basic_logger')
    logger.setLevel(logging.DEBUG)
    while True:
        repos = Repository.objects.exclude(pk__in=Commit.objects.values_list('repo', flat=True))
        for repo in repos:
            log_str = ''
            log_str = log(log_str, 'deploying repo: ' + repo.full_name)
            commit, created = Commit.objects.get_or_create(repo=repo, sha=get_latest_sha(repo))
            attempt = Attempt()
            attempt.commit = commit
            attempt.result = Result(name="Deploying")
            attempt.start_time = datetime.now()
            attempt.hostname = socket.gethostname()
            attempt.save()
            log_str = log(log_str, 'Downloading repo: ' + repo.full_name + commit.sha)
            try:
                 download(commit)
            except:
                print traceback.print_exc()
                save_attempt(attempt, "Download Error", log_str)
                continue
            remake_tmp_dir()
            directory_name = unzip()
            print directory_name
            log_str = log(log_str, 'directory_name = ' + directory_name)
            print 'type'
            print repo.repo_type.name
            if repo.repo_type.name == "Django":
                vagrant_pip_clear()
                #log_str = io.BytesIO()
                #ch = logging.StreamHandler(log_str)
                #ch.setLevel(logging.DEBUG)
                #ch.setFormatter(formatter)
                #logger.addHandler(ch)

                setup_files = search_file(directory_name, 'setup.py')
                log_str = log(log_str, 'setup.py: ' + str(setup_files))
                if len(setup_files):
                    save_attempt(attempt, "Not an Application", log_str)
                    continue

                setting_files = search_file(directory_name, 'settings.py')
                log_str = log(log_str, 'settings.py: ' + str(setting_files))
                if not len(setting_files):
                    save_attempt(attempt, "Missing Required Files", log_str)
                    continue
                elif len(setting_files) != 1:
                    save_attempt(attempt, "Duplicate Required Files", log_str)
                    continue
                
                commit.database = get_database(setting_files[0])
                commit.save()
                log_str = log(log_str, 'database: ' + commit.database.name)
                        
                manage_files = search_file(directory_name, 'manage.py')
                log_str = log(log_str, 'manage.py: ' + str(manage_files))
                if not len(manage_files):
                    save_attempt(attempt, "Missing Required Files", log_str)
                    continue
                elif len(manage_files) != 1:
                    save_attempt(attempt, "Duplicate Required Files", log_str)
                    continue

                requirement_files = search_file(directory_name, 'requirements.txt')
                log_str = log(log_str, 'requirements.txt' + str(requirement_files))

                try_deploy(manage_files[0], setting_files[0], requirement_file, attempt, log_str)
            elif repo.repo_type.name == "Ruby on Rails":
                print 'directory: ' + directory_name

                rakefiles = search_file(directory_name, 'Rakefile')
                if not rakefiles:
                    print 'no rakefile found'
                    save_attempt(attempt, "Missing Required Files", log_str)
                    continue
                rakefile_paths = [os.path.dirname(rakefile) for rakefile in rakefiles]
                #print 'rakefile_paths: ' + str(rakefile_paths)
                #elif len(rakefiles) != 1:
                #    print 'multiple rakefiles found'
                #    save_attempt(attempt, "Duplicate Required Files", log_str)
                #    continue
                print 'Finding database'
                gemfiles = search_file(directory_name, 'Gemfile')
                if not gemfiles:
                    print 'no gemfile'
                    save_attempt(attempt, "Missing Required Files", log_str)
                    continue
                gemfile_paths = [os.path.dirname(gemfile) for gemfile in gemfiles]
                #print 'gemfile_paths: ' + str(gemfile_paths)
                db_files = search_file(directory_name, 'database.yml')
                if not db_files:
                    print 'not use database'
                    save_attempt(attempt, "Missing Required Files", log_str)
                    continue

                print 'using database'
                db_file_paths = [os.path.dirname(os.path.dirname(db_file)) for db_file in db_files]
                #print 'db_file_paths: ' + str(db_file_paths)
                base_dirs = set.intersection(set(rakefile_paths), set(gemfile_paths), set(db_file_paths))
                if not base_dirs:
                    print 'can not find base directory'
                    save_attempt(attempt, "Missing Required Files", log_str)
                    continue
                base_dir = next(iter(base_dirs))
                print 'base_dir: ' + base_dir

                commit.database = get_database(os.path.join(base_dir, 'config/database.yml'))
                log_str = log(log_str, 'database: ' + commit.database.name)
                commit.save()
                rewrite_settings(base_dir, 'Ruby on Rails')

                try_deploy_ror(base_dir, attempt, log_str)
