#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import datetime
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()
from django.db.models import Q

from library.models import *
import utils

def remove_attempt(attempt):
    if attempt.repo.latest_attempt == attempt:
        attempt.repo.latest_attempt = None
    attempt.delete()

def remove_unuseful_attempts():
    reference_time = datetime.datetime.strptime('2016-01-01', '%Y-%m-%d')

    for repo in Repository.objects.all():
        if repo.latest_successful_attempt == None:
            for attempt in Attempt.objects.filter(repo = repo).exclude(result = 'OK'):
                if attempt.stop_time < reference_time:
                    remove_attempt(attempt)
        else:
            for attempt in Attempt.objects.filter(repo = repo).exclude(result = 'OK'):
                remove_attempt(attempt)

def main():
    remove_unuseful_attempts()

if __name__ == '__main__':
    main()
