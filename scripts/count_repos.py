#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
#sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

# stdlib imports
import time
import traceback
# django imports
from django.conf import settings
from django.db.models import Q
# project imports
from cmudbac.library.models import Attempt
from cmudbac.library.models import Repository
from cmudbac.core import utils


COMMITS_COUNT_THRESHOLD = 10


def count_deployed_repos():
    stats = {}
    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        if repo.commits_count >= 0 and repo.commits_count <= COMMITS_COUNT_THRESHOLD:
            continue
        if Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'key_column_usage'):
            stats[repo.project_type] = stats.get(repo.project_type, 0) + 1

    print(stats)

def count_ruby_failed_repos():
    count = 0
    for repo in Repository.objects.filter(latest_successful_attempt = None).filter(project_type = 2).exclude(latest_attempt = None):
        if repo.commits_count >= 0 and repo.commits_count <= COMMITS_COUNT_THRESHOLD:
            continue
        if 'Unable to find database.yml' in repo.latest_attempt.log:
            count += 1

    print(count)

def count_ruby_repetive_queries():
    repo_count = [0, 0]
    action_count = [0, 0]
    for repo in Repository.objects.exclude(latest_successful_attempt = None).filter(project_type = 2):
        repo_flag = False
        for action in Action.objects.filter(attempt = repo.latest_successful_attempt):
            action_flag = False
            for query in Query.objects.filter(action = action):
                if 'SELECT 1' in query.content:
                    repo_flag = True
                    action_flag = True
            if action_flag:
                action_count[0] += 1
            action_count[1] += 1
        if repo_flag:
            repo_count[0] += 1
        repo_count[1] += 1

    print(repo_count)
    print(action_count)

def count_wrong_marked_repos():
    repo_count = 0

    for repo in Repository.objects.exclude(latest_successful_attempt=None):
        if repo.latest_successful_attempt.result != 'OK':
            repo_count += 1
            repo.latest_successful_attempt = None
            repo.save()

    for repo in Repository.objects.filter(project_type=2):
        attempts = Attempt.objects.filter(repo=repo).filter(result='OK')
        attempts = list(attempts)
        if attempts:
            repo.latest_successful_attempt = attempts[-1]
            repo.save()

    print(repo_count)
    return

def main():
    # count_deployed_repos()
    # count_ruby_failed_repos()
    # count_ruby_repetive_queries()
    count_wrong_marked_repos()
    pass


if __name__ == '__main__':
    main()
