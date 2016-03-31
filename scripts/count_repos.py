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

def main():
    stats = {}
    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        if not Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'constraints'):
            stats[repo.project_type] = stats.get(repo.project_type, 0) + 1

    print stats
        

if __name__ == '__main__':
    main()
