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
            stats[s.description][project_type_name].append(s.count)
    
    dump_all_stats(directory, stats)

def column_stats(directory = '.'):
    stats = {'column_nullable': {}, 'column_type': {}, 'column_extra': {}}

    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        informations = Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'columns')
        if len(informations) == 0:
            continue
        information = informations[0]

        project_type_name = repo.project_type.name
        if project_type_name not in stats['column_nullable']:
            stats['column_nullable'][project_type_name] = {}
        if project_type_name not in stats['column_type']:
            stats['column_type'][project_type_name] = {}
        if project_type_name not in stats['column_extra']:
            stats['column_extra'][project_type_name] = {}

        if repo.latest_successful_attempt.database.name == 'PostgreSQL':
            regex = '(\(.*?\))[,\]]'
        elif repo.latest_successful_attempt.database.name == 'MySQL':
            regex = '(\(.*?\))[,\)]'
        for column in re.findall(regex, information.description):
            print column
            cells = column.split(',')
            
            nullable = str(cells[6]).replace("'", "").strip()
            stats['column_nullable'][project_type_name][nullable] = stats['column_nullable'][project_type_name].get(nullable, 0) + 1

            _type = str(cells[7]).replace("'", "").strip()
            stats['column_type'][project_type_name][_type] = stats['column_type'][project_type_name].get(_type, 0) + 1

            extra = str(cells[16]).replace("'", "").strip()
            if extra:
                stats['column_extra'][project_type_name][extra] = stats['column_extra'][project_type_name].get(extra, 0) + 1

    dump_all_stats(directory, stats)

def main():
    # active
    # table_stats(TABLES_DIRECTORY)
    # column_stats(TABLES_DIRECTORY)

    for explain in Explain.objects.all():
        print explain.query.content
        print explain.output

    # working
    
    # deprecated
if __name__ == '__main__':
    main()
