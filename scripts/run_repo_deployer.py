#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import datetime
import time
import pkgutil
import traceback
import urllib2
import shutil
import logging
import re
import io
import json
import socket

from os.path import join
from bs4 import BeautifulSoup
from string import Template

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

from crawler.models import *
from utils import *

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
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


def save_attempt(attempt, result, log_str, pkgs_from_f=[], pkgs_from_db=[]):
    attempt.result = Result(name=result)
    #attempt.log = log_str.getvalue()
    attempt.log = log_str
    
    attempt.duration = datetime.datetime.now()
    attempt.save()
    #log_str.close()
    for pkg in pkgs_from_f:
        dep = Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=Source(name='File'))
        pkg.count = pkg.count + 1
        pkg.save()
    for pkg in pkgs_from_db:
        Dependency.objects.get_or_create(attempt=attempt, package=pkg, source=Source(name='Database'))
## DEF

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



def deploy_repo(repo):
    log_str = ''
    

    if repo.repo_type.name == "Ruby on Rails":
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
                repo = Repository.objects.get(name=sys.argv[1])
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
