#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
import django
django.setup()

from crawler.models import *
import utils

def main():
    if len(sys.argv) != 3:
        return
    deploy_id = int(sys.argv[1])
    total_deployer = int(sys.argv[2])
    database = Database.objects.get(name='MySQL')

    for repo in Repository.objects.all():
        if repo.latest_attempt != None:
            continue
        if repo.id % total_deployer != deploy_id - 1:
            continue
        print 'Attempting to deploy {} using {} ...'.format(repo, repo.project_type.deployer_class)
        try:
            utils.vagrant_deploy(repo, database.name, deploy_id)
        except:
            pass

if __name__ == '__main__':
    main()
