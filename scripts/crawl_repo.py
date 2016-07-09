#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import time
import logging
logging.basicConfig(filename='repo_crawler.log',level=logging.DEBUG)
import json
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

import crawlers
from library.models import *
import utils

def add_module():
    if len(sys.argv) != 4:
        return
    module_name = sys.argv[1]
    package_name = sys.argv[2]
    package_type_id = sys.argv[3]
    package_version = sys.argv[4]
    try:    
        utils.add_module(module_name, package_name, package_type_id, package_version)
        print 'Successfully added new module {}'.format(module_name)
    except:
        print 'Failed to add new module {}'.format(repo_name)
        traceback.print_exc()

def add_repository():
    if len(sys.argv) != 4:
        return
    repo_name = sys.argv[1]
    repo_type_id = sys.argv[2]
    repo_setup_scripts = sys.argv[3]
    try:    
        utils.add_repo(repo_name, repo_type_id, repo_setup_scripts)
        print 'Successfully added new repository {}'.format(repo_name)
    except:
        print 'Failed to add new repository {}'.format(repo_name)
        traceback.print_exc()

def main():
    add_repository()
## IF


if __name__ == '__main__':
    main()