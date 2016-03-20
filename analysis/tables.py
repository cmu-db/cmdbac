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

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        statistics = Statistic.objects.filter(attempt = repo.latest_attempt)
        if len(statistics) == 0:
            continue
        
        for s in statistics:
            if s.description == 'num_transactions':
                continue
            if s.description not in stats:
                stats[s.description] = []
            stats[s.description].append(s.count)
    
    dump_all_stats(directory, stats)

def column_stats(directory = '.'):
    stats = {'column_nullable': {}, 'column_types': {}}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        informations = Information.objects.filter(attempt = repo.latest_attempt)
        if len(informations) == 0:
            continue

        for i in informations:
            if i.name == 'columns':
                if repo.latest_attempt.database.name == 'PostgreSQL':
                    for column in re.findall('(\(.*?\))[,\]]', i.description):
                        cells = column.split(',')
                        
                        nullable = str(cells[6]).replace("'", "").strip()
                        stats['nullable'][nullable] = stats['nullable'].get(nullable, 0) + 1

                        _type = str(cells[7]).replace("'", "").strip()
                        stats['types'][_type] = stats['types'].get(_type, 0) + 1
    
    dump_all_stats(directory, stats)
        
def constraint_stats(directory = '.'):
    stats = {'constraint_types': {}}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        informations = Information.objects.filter(attempt = repo.latest_attempt)
        if len(informations) == 0:
            continue

        for i in informations:
            if i.name == 'constraints':
                if repo.latest_attempt.database.name == 'MySQL':
                    for constraint in re.findall('(\(.*?\))[,\)]', i.description):
                        cells = constraint.split(',')

                        _type = str(cells[5])[:-1].replace("'", "").strip()
                        stats['types'][_type] = stats['types'].get(_type, 0) + 1

    dump_all_stats(directory, stats)

def main():
    table_stats(TABLES_DIRECTORY)
    column_stats(TABLES_DIRECTORY)
    constraint_stats(TABLES_DIRECTORY)

if __name__ == '__main__':
    main()
