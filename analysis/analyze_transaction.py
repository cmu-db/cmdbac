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
        project_type_name = repo.project_type.name
        for action in Action.objects.filter(attempt = repo.latest_successful_attempt):
            current_transaction = ''
            for query in Query.objects.filter(action = action):
                if current_transaction != '':
                    current_transaction += query.content + '\n'
                if 'BEGIN' in query.content:
                    assert(current_transaction == '')
                    current_transaction = query.content + '\n'
                if 'COMMIT' in query.content:
                    assert(current_transaction != '')
                    print current_transaction
                    current_transaction = ''
            
    dump_all_stats(directory, stats)
    

def main():
    # active
    transaction_stats(TRANSACTION_DIRECTORY)
    
    # working
    
    # deprecated
if __name__ == '__main__':
    main()
