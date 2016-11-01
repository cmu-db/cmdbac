#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

import re
import csv
import numpy as np
import sqlparse
import traceback
from utils import filter_repository, dump_all_stats, pickle_dump

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *

def foreign_key_stats(directory = '.'):
    stats = {'foreign_key_count': {}, 'foreign_key_type': {}}

    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        if filter_repository(repo):
            continue

        project_type_name = repo.project_type.name
        if project_type_name not in stats['foreign_key_count']:
            stats['foreign_key_count'][project_type_name] = []
        if project_type_name not in stats['foreign_key_type']:
                stats['foreign_key_type'][project_type_name] = {}
        if 0:    
            if project_type_name not in stats['join_key_constraint']:
                stats['join_key_constraint'][project_type_name] = {}

        informations = Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'columns')
        column_map = {}
        if len(informations) > 0:
            information = informations[0]
            if repo.latest_successful_attempt.database.name == 'PostgreSQL':
                regex = '(\(.*?\))[,\]]'
            elif repo.latest_successful_attempt.database.name == 'MySQL':
                regex = '(\(.*?\))[,\)]'

            for column in re.findall(regex, information.description):
                cells = column.split(',')
                table = str(cells[2]).replace("'", "").strip()
                name = str(cells[3]).replace("'", "").strip()
                _type = str(cells[7]).replace("'", "").strip()
                column_map[table + '.' + name] = _type
                column_map[name] = _type

        key_column_usage_informations = Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'key_column_usage')
        constraint_informations = Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'constraints')
        constraint_map = {}
        if len(key_column_usage_informations) > 0 and len(constraint_informations) > 0:
            if repo.latest_successful_attempt.database.name == 'PostgreSQL':
                regex = '(\(.*?\))[,\]]'
            elif repo.latest_successful_attempt.database.name == 'MySQL':
                regex = '(\(.*?\))[,\)]'
            
            merge_map = {}
            key_column_usage_information = key_column_usage_informations[0]
            for column in re.findall(regex, key_column_usage_information.description):
                cells = column.split(',')
                constraint_name = str(cells[2]).replace("'", "").strip()
                table_name = str(cells[5]).replace("'", "").strip()
                column_name = str(cells[6]).replace("'", "").strip()
                merge_map_key = table_name + '.' + constraint_name 
                if merge_map_key in merge_map:
                    merge_map[merge_map_key].append(column_name)
                else:
                    merge_map[merge_map_key] = [column_name]

            constraint_information = constraint_informations[0]
            for column in re.findall(regex, constraint_information.description):
                cells = column.split(',')
                constraint_name = str(cells[2]).replace("'", "").strip()
                if repo.latest_successful_attempt.database.name == 'PostgreSQL':
                    table_name = str(cells[5]).replace("'", "").strip()
                    constraint_type = str(cells[6]).replace("'", "").strip()
                elif repo.latest_successful_attempt.database.name == 'MySQL':
                    table_name = str(cells[4]).replace("'", "").strip()
                    constraint_type = str(cells[5])[:-1].replace("'", "").strip()
                merge_map_key =  table_name + '.' + constraint_name
                if merge_map_key in merge_map:
                    for column_name in merge_map[merge_map_key]:
                        constraint_map[table_name + '.' + column_name] = constraint_type
                        constraint_map[column_name] = constraint_type

                        if constraint_type == 'FOREIGN KEY':
                            _type = column_map[table_name + '.' + column_name]
                            stats['foreign_key_type'][project_type_name][_type] = stats['foreign_key_type'][project_type_name].get(_type, 0) + 1
                            
            for action in Action.objects.filter(attempt = repo.latest_successful_attempt):
                queries = Query.objects.filter(action = action)
                foreign_key_count = 0

                for query in queries:
                    parsed = sqlparse.parse(query.content)[0]
                    tokens = parsed.tokens

                    for token in tokens:
                        if isinstance(token, sqlparse.sql.Identifier):
                            token_name = token.value.replace('"', '').replace('`', '')
                            if token_name in constraint_map:
                                constraint = constraint_map[token_name]
                                if constraint == 'FOREIGN KEY':
                                    foreign_key_count += 1

                    for explain in Explain.objects.filter(query = query):
                        if 'FOREIGN' in explain.output:
                            print explain.output

                stats['foreign_key_count'][project_type_name].append(foreign_key_count)

    dump_all_stats(directory, stats)

def main():
    foreign_key_stats()

if __name__ == '__main__':
    main()
