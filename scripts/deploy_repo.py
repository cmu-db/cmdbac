#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import time
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()
from django.db.models import Q

from library.models import *
import utils

def main():
    if len(sys.argv) < 3:
        return
    deploy_id = int(sys.argv[1])
    repo_name = sys.argv[2]
    if len(sys.argv) >= 4:
        database_name = sys.argv[3]
    else:
        database_name = 'MySQL'
    database = Database.objects.get(name = database_name)

    repo = Repository.objects.get(name = repo_name)
    print 'Attempting to deploy {} using {} ...'.format(repo, repo.project_type.deployer_class)
    try:
        utils.vagrant_deploy(repo, deploy_id, database)
    except:
        traceback.print_exc()

if __name__ == '__main__':
    main()
