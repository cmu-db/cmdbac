#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
#sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

# setup django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

# stdlib imports
import argparse
import json
import logging ; logging.basicConfig(filename='repo_crawler.log',level=logging.DEBUG)
import time
import traceback
# django imports
from django.conf import settings
# project imports
from cmudbac.core import utils
from cmudbac.library.models import CrawlerStatus
import cmudbac.core.crawlers


def add_module():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='Adds a module to the system.')
    parser.add_argument('module_name')
    parser.add_argument('package_name')
    parser.add_argument('package_type_id')
    parser.add_argument('package_version')
    args = parser.parse_args()

    try:
        utils.add_module(args.module_name, args.package_name, args.package_type_id, args.package_version)
        print('Successfully added new module {}'.format(module_name))
    except:
        print('Failed to add new module {}'.format(repo_name))
        traceback.print_exc()

    return

def add_repository():
    parser = argparse.ArgumentParser(description='Adds a module to the system.')
    parser.add_argument('repo_name')
    parser.add_argument('repo_type_id')
    args = parser.parse_args()

    try:
        utils.add_repo(args.repo_name, args.repo_type_id, None)
        print('Successfully added new repository {}'.format(repo_name))
    except:
        print('Failed to add new repository {}'.format(repo_name))
        traceback.print_exc()
    return


def main():
    # add_module()
    add_repository()
    return


if __name__ == '__main__':
    main()
