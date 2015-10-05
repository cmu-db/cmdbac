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

def main():
    database = Database.objects.get(name='MySQL')

    for repo in Repository.objects.filter(project_type_id = 1):
        print 'Attempting to deploy {} using {} ...'.format(repo, repo.project_type.deployer_class)
        try:
            utils.vagrant_deploy(repo, database.name)
        except:
            pass

if __name__ == '__main__':
    main()