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
    project_type = int(sys.argv[1])
    deploy_id = int(sys.argv[2])
    total_deployer = int(sys.argv[3])
    database = Database.objects.get(name='MySQL')

    for repo in Repository.objects.filter(project_type = project_type).filter(Q(latest_attempt__result = 'DE') | Q(latest_attempt__result = 'OK')):
    # for repo in Repository.objects.filter(project_type = 1).filter(latest_attempt__result = 'OK').filter(latest_attempt__log__contains = "[Errno 13] Permission denied: '/var/log/mysql/mysql.log'"):
        if repo.id % total_deployer != deploy_id - 1:
            continue
        n = len(Attempt.objects.filter(repo = repo).filter(result = 'OK'))
        if n == 0:
            continue
        m = len(Action.objects.filter(attempt = repo.latest_attempt))
        if m != 0:
            continue
        print 'Attempting to deploy {} using {} ...'.format(repo, repo.project_type.deployer_class)
        try:
            utils.vagrant_deploy(repo, deploy_id, database)
        except:
            pass
        finally:
            time.sleep(5)

if __name__ == '__main__':
    main()
