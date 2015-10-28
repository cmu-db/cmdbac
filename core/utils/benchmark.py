#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
import django
django.setup()

import traceback

import crawlers
from crawler.models import *
import utils

def run_benchmark(attempt_id, database, benchmark):
	# run the benchmark
    attempt = Attempt.objects.get(id=attempt_id)
    repo = attempt.repo
    deploy_id = 1
    print 'Running benchmark for attempt {} using {} ...'.format(attempt.id, repo.project_type.deployer_class)
    try:
        utils.vagrant_benchmark(repo, deploy_id, database, benchmark)
    except Exception, e:
        traceback.print_exc()