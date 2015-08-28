#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

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
from itertools import chain

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
import django
django.setup()

from crawler.models import *
from deployers import *
import utils

copied_dir = ['crawler', 'db_webcrawler', 'core']
vagrant_dir = os.path.join(os.path.dirname(__file__), os.pardir, 'vagrant')
copied_files = []

def vagrant_setup():
    print ('Setuping Vagrant ...')

    ## Copy files
    for new_dir in copied_dir:
        old_dir = os.path.join(os.path.dirname(__file__), os.pardir, new_dir)
        shutil.copytree(old_dir, os.path.join(os.path.dirname(__file__), new_dir))

    for f in os.listdir(vagrant_dir):
        if not f.startswith('.'):
            copied_files.append(f)
            shutil.copy2(os.path.join(vagrant_dir, f), os.path.dirname(__file__))

    utils.run_command('cd {} && {}'.format(sys.path[0], 'vagrant up'))

def vagrant_clear():
    # Delete files
    for new_dir in copied_dir:
        try:
            shutil.rmtree(os.path.join(os.path.dirname(__file__), new_dir))
        except:
            pass

    for f in copied_files:
        try:
            os.remove(os.path.join(os.path.dirname(__file__), f))
        except:
            pass

    utils.run_command('cd {} && {}'.format(sys.path[0], 'vagrant halt'))

def set_vagrant_database():
    settings_file = os.path.join(os.path.dirname(__file__), "db_webcrawler", "settings.py")
    settings = open(settings_file).read()
    if "'HOST': 'localhost'" in settings:
        settings = settings.replace("'HOST': 'localhost'", "'HOST': '10.0.2.2'")
        fout = open(settings_file, 'w')
        fout.write(settings)
        fout.flush()
        fout.close()

def unset_vagrant_database():
    settings_file = os.path.join(os.path.dirname(__file__), "db_webcrawler", "settings.py")
    settings = open(settings_file).read()
    if "'HOST': '10.0.2.2'" in settings:
        settings = settings.replace("'HOST': 'localhost'", "'HOST': 'localhost'")
        fout = open(settings_file, 'w')
        fout.write(settings)
        fout.flush()
        fout.close()

def vagrant_deploy(repo, database):
    set_vagrant_database()
    out = os.system('cd {} && {}'.format(
        sys.path[0],
        'vagrant ssh -c "{}"'.format(
            'python /vagrant/core/scripts/vagrant_deploy.py {} {}'.format(repo, database))))
    unset_vagrant_database()

    return out

def main():
    logger = logging.getLogger('basic_logger')
    logger.setLevel(logging.DEBUG)

    vagrant_clear()
    vagrant_setup()
        
    while True:
        # repos = Repository.objects.filter(name='acecodes/acetools') 
        # repos = Repository.objects.filter(name='adamgillfillan/mental_health_app')
        repos = Repository.objects.filter(name='aae4/btw')

        database = Database.objects.get(name='SQLite3')
        
        for repo in repos:
            print 'Attempting to deploy {} using {} ...'.format(repo, repo.project_type.deployer_class)
            vagrant_deploy(repo, database.name)
            break
        ## FOR
        break
    ## WHILE

    vagrant_clear()

def test():
    logger = logging.getLogger('basic_logger')
    logger.setLevel(logging.DEBUG)

    vagrant_clear()
    vagrant_setup()
        
    result = 0

    while True:
        repos = Repository.objects.filter(name='acecodes/acetools') 
        repos = repos | Repository.objects.filter(name='adamgillfillan/mental_health_app')
        repos = repos | Repository.objects.filter(name='aae4/btw')

        database = Database.objects.get(name='SQLite3')
        
        for repo in repos:
            print 'Attempting to deploy {} using {} ...'.format(repo, repo.project_type.deployer_class)
            result = vagrant_deploy(repo, database.name)
            if result != 0:
                break
        ## FOR
        break
    ## WHILE

    vagrant_clear()

    print '############'
    if result == 0:
        print 'TEST PASSED!'
    else:
        print 'TEST FAILED!'
    print '############'

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != 'test':
        main()
    else:
        test()
