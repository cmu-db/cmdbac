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

COMMITS_COUNT_THRESHOLD = 10

def count_deployed_repos():
    stats = {}
    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        if repo.commits_count >= 0 and repo.commits_count <= COMMITS_COUNT_THRESHOLD:
            continue
        if Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'key_column_usage'):
            stats[repo.project_type] = stats.get(repo.project_type, 0) + 1

    print stats

def count_ruby_failed_repos():
    count = 0
    for repo in Repository.objects.exclude(latest_successful_attempt = None).filter(project_type = 2):
        if repo.commits_count >= 0 and repo.commits_count <= COMMITS_COUNT_THRESHOLD:
            continue
        if 'Unable to find database.yml' in repo.latest_attempt.log:
            count += 1

    print count

def main():
    # count_deployed_repos()
    count_ruby_failed_repos()
        

if __name__ == '__main__':
    main()
