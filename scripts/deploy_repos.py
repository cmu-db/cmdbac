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

def deploy_valid_repos():
    if len(sys.argv) != 5:
        return
    project_type = int(sys.argv[1])
    deploy_id = int(sys.argv[2])
    total_deployer = int(sys.argv[3])
    database = Database.objects.get(name=sys.argv[4])
    
    for repo in Repository.objects.filter(project_type = project_type):
    # for repo in Repository.objects.filter(project_type = project_type).exclude(Q(latest_attempt__result = 'DE') | Q(latest_attempt__result = 'OK')):
    # for repo in Repository.objects.filter(project_type = 1).filter(latest_attempt__result = 'OK').filter(latest_attempt__log__contains = "[Errno 13] Permission denied: '/var/log/mysql/mysql.log'"):
        if repo.id % total_deployer != deploy_id - 1:
            continue
        if Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'key_column_usage'):
            continue
        print 'Attempting to deploy {} using {} ...'.format(repo, repo.project_type.deployer_class)
        try:
            utils.vagrant_deploy(repo, deploy_id, database)
        except:
            traceback.print_exc()
        finally:
            time.sleep(5)

# From http://augustwu.iteye.com/blog/554827
from functools import wraps
import errno
import os
import signal

class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator

@timeout(1000)
def deploy_with_timeout(repo, deploy_id, database):
    utils.vagrant_deploy(repo, deploy_id, database)

def deploy_failed_ruby_repos():
    project_type = 2
    deploy_id = int(sys.argv[1])
    total_deployer = int(sys.argv[2])
    database = Database.objects.get(name=sys.argv[3])
    
    for repo in Repository.objects.filter(project_type = project_type):
        if repo.id % total_deployer != deploy_id - 1:
            continue
        if Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'key_column_usage'):
            continue
        if repo.latest_attempt == None or 'Unable to find database.yml' in repo.latest_attempt.log or 'Access denied for user' in repo.latest_attempt.log:
            print 'Attempting to deploy {} using {} ...'.format(repo, repo.project_type.deployer_class)
            try:
                deploy_with_timeout(repo, deploy_id, database)
            except:
                traceback.print_exc()
            finally:
                time.sleep(5)

def main():
    # deploy_valid_repos()
    deploy_failed_ruby_repos()

if __name__ == '__main__':
    main()
