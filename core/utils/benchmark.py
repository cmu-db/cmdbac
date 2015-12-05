#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()
from library.models import *
import utils

def run_benchmark(attempt_id, database, benchmark):
	# run the benchmark
    deploy_id = 1
    print 'Running benchmark for attempt {}'.format(attempt_id)
    try:
        utils.vagrant_benchmark(attempt_id, deploy_id, database, benchmark)
    except Exception, e:
        traceback.print_exc()