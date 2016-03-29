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

TABLES_DIRECTORY = 'tables'

def table_stats(directory = '.'):
    stats = {}

    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        statistics = Statistic.objects.filter(attempt = repo.latest_successful_attempt)
        if len(statistics) == 0:
            continue
        
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
            stats[s.description][repo.project_type.name].append(s.count)
    
    dump_all_stats(directory, stats, True)

def column_stats(directory = '.'):
    stats = {'column_nullable': {}, 'column_types': {}}

    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        informations = Information.objects.filter(attempt = repo.latest_successful_attempt)
        if len(informations) == 0:
            continue

        for i in informations:
            if i.name == 'columns':
                if repo.latest_successful_attempt.database.name == 'PostgreSQL':
                    for column in re.findall('(\(.*?\))[,\]]', i.description):
                        cells = column.split(',')
                        
                        nullable = str(cells[6]).replace("'", "").strip()
                        stats['column_nullable'][nullable] = stats['column_nullable'].get(nullable, 0) + 1

                        _type = str(cells[7]).replace("'", "").strip()
                        stats['column_types'][_type] = stats['column_types'].get(_type, 0) + 1
    
    dump_all_stats(directory, stats)

def main():
    # active
    table_stats(TABLES_DIRECTORY)

    # working
    column_stats(TABLES_DIRECTORY)

    # deprecated
if __name__ == '__main__':
    main()
