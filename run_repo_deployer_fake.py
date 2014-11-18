#!/usr/bin/env python
import os
from os.path import join
from utils import run_command, query
from datetime import datetime
import time
import pkgutil
import traceback
from string import Template
import urllib2
import shutil
import logging
import random

logging.basicConfig(filename='repo_deployer.log',level=logging.DEBUG)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

import django
django.setup()

from crawler.models import *

if __name__ == '__main__':
    result_list = list(Result.objects.all())
    while True:
        repos = Repository.objects.exclude(pk__in=Attempt.objects.values_list('repo', flat=True))
        for repo in repos:
            log = ''
            print 'deploying repo: ' + repo.full_name
            log = log + 'deploying repo: ' + repo.full_name + '\n'
            attempt = Attempt()
            attempt.repo = repo
            attempt.time = datetime.now()
            attempt.result = random.choice(result_list)
            attempt.log = attempt.result.name
            attempt.save()
            repo.last_attempt = attempt
            repo.save()

