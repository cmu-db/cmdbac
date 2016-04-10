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
        column_informations = Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'columns')
        constraint_informations = Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'constraints')
        
        if len(column_informations) > 0 and len(constraint_informations) > 0:
            column_information = column_informations[0]
            constraint_information = constraint_informations[0]

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
            
            for column in re.findall(regex, column_information.description):
                cells = column.split(',')
                
                nullable = str(cells[6]).replace("'", "").strip()
                stats['column_nullable'][project_type_name][nullable] = stats['column_nullable'][project_type_name].get(nullable, 0) + 1

                _type = str(cells[7]).replace("'", "").strip()
                stats['column_type'][project_type_name][_type] = stats['column_type'][project_type_name].get(_type, 0) + 1

                extra = str(cells[16]).replace("'", "").strip()
                if extra:
                    stats['column_extra'][project_type_name][extra] = stats['column_extra'][project_type_name].get(extra, 0) + 1

            for column in re.findall(regex, constraint_information.description):
                cells = column.split(',')
                if repo.latest_successful_attempt.database.name == 'PostgreSQL':
                    constraint_type = str(cells[6]).replace("'", "").strip()
                elif repo.latest_successful_attempt.database.name == 'MySQL':
                    constraint_type = str(cells[5])[:-1].replace("'", "").strip()
                stats['column_extra'][project_type_name][constraint_type] = stats['column_extra'][project_type_name].get(constraint_type, 0) + 1

    dump_all_stats(directory, stats)

def main():
    # active
    table_stats(TABLES_DIRECTORY)
    column_stats(TABLES_DIRECTORY)
    
    # working
    
    # deprecated
if __name__ == '__main__':
    main()
