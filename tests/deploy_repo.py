#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()
from django.db.models import Q

from library.models import *
import utils

def main():
    if len(sys.argv) != 4:
        return
    deploy_id = int(sys.argv[1])
    repo_name = sys.argv[2]
    database = Database.objects.get(name = sys.argv[3])

    repo = Repository.objects.get(name = repo_name)
    print 'Attempting to deploy {} using {} ...'.format(repo, repo.project_type.deployer_class)
    try:
        utils.vagrant_deploy(repo, deploy_id, database)
    except:
        pass

if __name__ == '__main__':
    main()
