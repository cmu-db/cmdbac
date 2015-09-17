#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
import django
django.setup()

from crawler.models import *
from deployers import *
import utils

def test():
    vagrant_clear()
    vagrant_setup()
        
    result = 0

    while True:
        repos = Repository.objects.filter(name='acecodes/acetools') 
        repos = repos | Repository.objects.filter(name='adamgillfillan/mental_health_app')
        repos = repos | Repository.objects.filter(name='aae4/btw')

        database = Database.objects.get(name='MySQL')
        
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
    if len(sys.argv) == 2 and sys.argv[1] == 'test':
        test()