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

def download(repo):
    url = 'https://github.com/django/django/archive/06726965c3e53e9a6b87e1532951a93d5f94f426.zip'
    #url = 'https://api.github.com/repos/' + repo.full_name + '/tarball'
#    request = urllib2.Request(url)
#    request.add_header('Authorization', 'token %s' % token)
    response = query(url)
    tar_file = 'tmp.zip'
    tarFile = open(tar_file, 'wb')
    shutil.copyfileobj(response.fp, tarFile)
    tarFile.close()

if __name__ == '__main__':
    if $2 == None:
        repo = Ropository.objects.filter(repo__full_name=$1).order_by('-local_id')[0]
    else:

        repo = Repository.objects.get(repo__full_name=$1, local_id=$2)
    
   repo = models.ForeignKey('Repository')
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

