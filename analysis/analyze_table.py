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
            if s.description not in stats:
                stats[s.description] = {}
            project_type_name = repo.project_type.name
            if project_type_name not in stats[s.description]:
                stats[s.description][project_type_name] = []
            stats[s.description][project_type_name].append(s.count)
    
    dump_all_stats(directory, stats)

def column_stats(directory = '.'):
    stats = {'column_nullable': {}, 'column_type': {}, 'column_extra': {}, 'column_num': {}}

    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        column_informations = Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'columns')
        constraint_informations = Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'constraints')
        num_table_statistics = Statistic.objects.filter(attempt = repo.latest_successful_attempt).filter(description = 'num_tables')

        if len(column_informations) > 0 and len(constraint_informations) > 0 and len(num_table_statistics) > 0:
            column_information = column_informations[0]
            constraint_information = constraint_informations[0]
            num_tables = num_table_statistics[0].count

            project_type_name = repo.project_type.name
            if project_type_name not in stats['column_nullable']:
                stats['column_nullable'][project_type_name] = {}
            if project_type_name not in stats['column_type']:
                stats['column_type'][project_type_name] = {}
            if project_type_name not in stats['column_extra']:
                stats['column_extra'][project_type_name] = {}
            if project_type_name not in stats['column_num']:
                stats['column_num'][project_type_name] = []

            if repo.latest_successful_attempt.database.name == 'PostgreSQL':
                regex = '(\(.*?\))[,\]]'
            elif repo.latest_successful_attempt.database.name == 'MySQL':
                regex = '(\(.*?\))[,\)]'
            
            table_stats = {'column_nullable': {}, 'column_type': {}, 'column_extra': {}, 'column_num': {}}
            for column in re.findall(regex, column_information.description):
                cells = column.split(',')

                table = str(cells[2]).replace("'", "").strip()
                
                nullable = str(cells[6]).replace("'", "").strip()
                if table not in table_stats['column_nullable']:
                    table_stats['column_nullable'][table] = {}
                table_stats['column_nullable'][table][nullable] = table_stats['column_nullable'][table].get(nullable, 0) + 1
                # stats['column_nullable'][project_type_name][nullable] = stats['column_nullable'][project_type_name].get(nullable, 0) + 1.0 / num_tables

                _type = str(cells[7]).replace("'", "").strip()
                if table not in table_stats['column_type']:
                    table_stats['column_type'][table] = {}
                table_stats['column_type'][table][_type] = table_stats['column_type'][table].get(_type, 0) + 1
                # stats['column_type'][project_type_name][_type] = stats['column_type'][project_type_name].get(_type, 0) + 1.0 / num_tables

                extra = str(cells[16]).replace("'", "").strip()
                if extra:
                    if table not in table_stats['column_extra']:
                        table_stats['column_extra'][table] = {}
                    table_stats['column_extra'][table][extra] = table_stats['column_extra'][table].get(extra, 0) + 1
                
                if table not in table_stats['column_num']:
                    table_stats['column_num'][table] = 0
                table_stats['column_num'][table] += 1
                
                # stats['column_extra'][project_type_name][extra] = stats['column_extra'][project_type_name].get(extra, 0) + 1.0 / num_tables

                # stats['column_num'][project_type_name]['TOTAL'] =  stats['column_num'][project_type_name].get('TOTAL', 0) + 1


            for column in re.findall(regex, constraint_information.description):
                cells = column.split(',')
                if repo.latest_successful_attempt.database.name == 'PostgreSQL':
                    constraint_type = str(cells[6]).replace("'", "").strip()
                elif repo.latest_successful_attempt.database.name == 'MySQL':
                    constraint_type = str(cells[5])[:-1].replace("'", "").strip()
                if repo.latest_successful_attempt.database.name == 'PostgreSQL':
                    table = str(cells[5]).replace("'", "").strip()
                elif repo.latest_successful_attempt.database.name == 'MySQL':
                    table = str(cells[4]).replace("'", "").strip()
                if table not in table_stats['column_extra']:
                    table_stats['column_extra'][table] = {}
                table_stats['column_extra'][table][constraint_type] = table_stats['column_extra'][table].get(constraint_type, 0) + 1

            for stats_type in table_stats:
                for table in table_stats[stats_type]:
                    if isinstance(table_stats[stats_type][table], dict):
                        for second_type in table_stats[stats_type][table]:
                            if second_type not in stats[stats_type][project_type_name]:
                                stats[stats_type][project_type_name][second_type] = []
                            stats[stats_type][project_type_name][second_type].append(table_stats[stats_type][table][second_type])
                    else:
                        stats[stats_type][project_type_name].append(table_stats[stats_type][table])

    dump_all_stats(directory, stats)

def main():
    # active
    table_stats(TABLES_DIRECTORY)
    column_stats(TABLES_DIRECTORY)
    
    # working
    
    # deprecated
if __name__ == '__main__':
    main()
