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
import time
import traceback
# django imports
from django.db.models import Q
# project imports
from cmudbac.core import utils
from cmudbac.library.models import Database


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='Deploys a repo to the vagrant system.')
    parser.add_argument('deploy_id', type=int)
    parser.add_argument('repo_name')
    parser.add_argument('database_name', default='MySQL', nargs='?')

    # get database
    database = Database.objects.get(name=database_name)

    # get repo
    repo = Repository.objects.get(name=repo_name)

    print('Attempting to deploy {} using {} ...'.format(repo, repo.project_type.deployer_class))

    try:
        utils.vagrant_deploy(repo, deploy_id, database)
    except:
        traceback.print_exc()
    return


if __name__ == '__main__':
    main()
