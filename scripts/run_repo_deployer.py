#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "core"))

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
from string import Template

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
import django
django.setup()

from crawler.models import *
from deployers import *
from utils import *

def vagrant_deploy(repo, database):
    print repo, database
    return 
    os.system('vagrant ssh -c "{}"'.format(
        'python /vagrant/vagrant_deploy.py {} {}'.format(repo, database)))

def main():
    logger = logging.getLogger('basic_logger')
    logger.setLevel(logging.DEBUG)
        
    while True:
        repos = Repository.objects.filter(name='acecodes/acetools')
        database = Database.objects.get(name='SQLite3')
        
        for repo in repos:
             
            print 'Attempting to deploy {} using {} ...'.format(repo, repo.project_type.deployer_class)
            vagrant_deploy(repo, database.name)
            break
        ## FOR
        break
    ## WHILE

if __name__ == '__main__':
    main()
