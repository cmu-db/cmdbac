#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import re
import csv
from dump import dump_all_stats

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *

TRANSACTION_DIRECTORY = 'tables'

def transaction_stats(directory = '.'):
    stats = {}

    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        for s in statistics:
            if s.description == 'num_transactions':
                continue
            if s.count == 0:
                continue
            if s.description not in stats:
                stats[s.description] = {}
            project_type_name = repo.project_type.name
            if project_type_name not in stats[s.description]:
                stats[s.description][project_type_name] = []
            stats[s.description][project_type_name].append(s.count)
    
    dump_all_stats(directory, stats)
    

def main():
    # active
    transaction_stats(TRANSACTION_DIRECTORY)
    
    # working
    
    # deprecated
if __name__ == '__main__':
    main()
