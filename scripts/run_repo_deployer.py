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

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
repo_deployer_logger = logging.getLogger('repo_deployer')
repo_deployer_logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
ch.setFormatter(formatter)
repo_deployer_logger.addHandler(ch)


def main():
    logger = logging.getLogger('basic_logger')
    logger.setLevel(logging.DEBUG)
        
    while True:
        #repos = Repository.objects.exclude(pk__in=Attempt.objects.values_list('repo', flat=True))
        
        repos = Repository.objects.filter(name="aae4/btw")
        database = Database.objects.get(name='SQLite3')
        
        # if string:
        #    repos = repos.filter(repo_type__name=string)
        for repo in repos:
             
            moduleName = "deployers.%s" % (repo.project_type.deployer_class.lower())
            moduleHandle = __import__(moduleName, globals(), locals(), [repo.project_type.deployer_class])
            klass = getattr(moduleHandle, repo.project_type.deployer_class)
            
            print "Attempting to deploy", repo, "using", repo.project_type.deployer_class
            deployer = klass(repo, database)
            deployer.deploy()
            break
        ## FOR
        break
    ## WHILE

if __name__ == '__main__':
    main()
