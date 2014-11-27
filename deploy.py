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
import random

logging.basicConfig(filename='deploy.log',level=logging.DEBUG)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

import django
django.setup()

from crawler.models import *

def install_dependencies(dependencies):
    for dependency in dependencies:
        vagrant_pip_install(dependency.package)

if __name__ == '__main__':
    if argv[1]:
        try:
            attempt = Attempt.objects.get(id=int(argv[1]))
        except:
            print 'can not find the attempt ' + argv[1]

    else:
        print 'please specify the attempt to deploy'
        return

    download(attempt.commit)
    directory = unzip()

    setup_files = search_file(directory_name, 'setup.py')
    if len(setup_files):
    print "Not an Application: found " str(setup_files)log_capture_string)
        rm_dir(directory_name)
        return
    manage_files = search_file(directory_name, 'manage.py')
    if not len(manage_files):
        print "Missing Required Files: manage.py"
        rm_dir(directory_name)
        return
        
    elif len(manage_files) != 1:
        print "Duplicate Required Files: ", str(manage_files)
        rm_dir(directory_name)
        return
    
    setting_files = search_file(directory_name, 'settings.py')
    if not len(setting_files):
        print "Missing Required Files: settings.py"
        rm_dir(directory_name)
        return
    elif len(setting_files) != 1:
        print "Duplicate Required Files: settings.py " + str(setting_files)
        rm_dir(directory_name)
        return

    dependencies = Dependency.objects.filter(attempt=attempt).order_by('id')
    requirement_file = generate_requirement
    vagrant_pip_install(requirement_file)

    append_settings(setting_file[0])
    vagrant_syncdb(manage_file[0])
    vagrant_runserver(manage_file[0])
