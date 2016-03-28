#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import re
import csv
import numpy as np
import sqlparse
from dump import dump_stats, dump_all_stats

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *

QUERIES_DIRECTORY = 'queries'

def query_stats(directory = '.'):
    stats = {'query_type': {}}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        actions = Action.objects.filter(attempt = repo.latest_attempt)
        if len(actions) == 0:
            continue
        
        for action in actions:
            counters = Counter.objects.filter(action = action)
            for counter in counters:
                project_type_name = repo.project_type.name
                if project_type_name not in stats['query_type']:
                    stats['query_type'][project_type_name] = {}
                if counter.description not in stats['query_type'][project_type_name]:
                    stats['query_type'][project_type_name][counter.description] = 0
                stats['query_type'][project_type_name][counter.description] += counter.count

    dump_all_stats(directory, stats)

def coverage_stats(directory = '.'):
    stats = {'table_coverage': {}, 'column_coverage': {}, 'index_coverage': {}}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        actions = Action.objects.filter(attempt = repo.latest_attempt)
        if len(actions) == 0:
            continue
        statistics = Statistic.objects.filter(attempt = repo.latest_attempt).filter(description = 'num_tables')
        if len(statistics) == 0:
            continue
        table_count = statistics[0].count
        if table_count == 0:
            continue

        project_type_name = repo.project_type.name
        
        covered_tables = set()
        for action in actions:
            for query in Query.objects.filter(action = action):
                for table in re.findall('FROM\s*\S+', query.content.upper()):
                    table_name = table.replace('FROM', '').replace("'", "").replace(' ', '').replace('"', '')
                    if '(' in table_name or ')' in table_name:
                        continue
                    covered_tables.add(table_name)

        table_percentage = int(float(len(covered_tables) * 100) / table_count)
        table_percentage = min(table_percentage, 100)

        if project_type_name not in stats['table_coverage']:
            stats['table_coverage'][project_type_name] = []
        stats['table_coverage'][project_type_name].append(table_percentage)

        informations = Information.objects.filter(attempt = repo.latest_attempt).filter(name = 'columns')
        if len(informations) > 0:
            information = informations[0]
            column_count = 0
            for covered_table in covered_tables:
                column_count += len(re.findall(covered_table.upper(), information.description.upper()))
            if repo.latest_attempt.database.name == 'PostgreSQL':
                column_count = min(column_count, len(re.findall('(\(.*?\))[,\]]', information.description)))
            elif repo.latest_attempt.database.name == 'MySQL':
                column_count = min(column_count, len(re.findall('(\(.*?\))[,\)]', information.description)))
        
            if column_count > 0:
                covered_columns = set()
                for action in actions:
                    for query in Query.objects.filter(action = action):
                        parsed = sqlparse.parse(query.content)[0]
                        tokens = parsed.tokens
                        for token in tokens:
                            if isinstance(token, sqlparse.sql.Identifier):
                                covered_columns.add(token.value)

                column_percentage = int(float(len(covered_columns) * 100) / column_count)
                column_percentage = min(column_percentage, 100)

                if project_type_name not in stats['column_coverage']:
                    stats['column_coverage'][project_type_name] = []
                stats['column_coverage'][project_type_name].append(column_percentage)

        informations = Information.objects.filter(attempt = repo.latest_attempt).filter(name = 'indexes')
        if len(informations) > 0:
            information = informations[0]
            index_count = 0
            for covered_table in covered_tables:
                index_count += len(re.findall(covered_table.upper(), information.description.upper()))
            statistics = Statistic.objects.filter(attempt = repo.latest_attempt).filter(description = 'num_indexes')
            if len(statistics) == 0:
                continue
            if statistics[0].count > 0:
                index_count = min(index_count, statistics[0].count)
            
            if index_count > 0:
                covered_indexes = set()
                for action in actions:
                    for query in Query.objects.filter(action = action):
                        for explain in Explain.objects.filter(query = query):
                            for raw_index in re.findall('Index.*?Scan.*?on \S+', explain.output):
                                index = raw_index.split()[-1]
                                covered_indexes.add(index)
                   
                index_percentage = int(float(len(covered_indexes) * 100) / index_count)
                index_percentage = min(index_percentage, 100)

                if project_type_name not in stats['index_coverage']:
                    stats['index_coverage'][project_type_name] = []
                stats['index_coverage'][project_type_name].append(index_percentage)

    dump_all_stats(directory, stats)

def sort_stats(directory = '.'):
    stats = {'sort_keys': {}}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        project_type_name = repo.project_type.name
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            for query in Query.objects.filter(action = action):
                for explain in Explain.objects.filter(query = query):
                    for sort_keys in re.findall('Sort Key: .*', explain.output):
                        sort_keys_count = len(re.findall(',', sort_keys)) + 1
                        if project_type_name not in stats['sort_keys']:
                            stats['sort_keys'][project_type_name] = {}
                        if sort_keys_count <= 3:
                            stats['sort_keys'][project_type_name][str(sort_keys_count)] = stats['sort_keys'][project_type_name].get(str(sort_keys_count), 0) + 1
                        else:
                            stats['sort_keys'][project_type_name]['greater than or equal to 4'] = stats['sort_keys'][project_type_name].get('greater than or equal to 4', 0) + 1

    dump_all_stats(directory, stats)

def join_stats(directory = '.'):
    stats = {}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            queries = Query.objects.filter(action = action)
            for query in queries:
                content = query.content.upper()
                if 'JOIN' in content:
                    parsed = sqlparse.parse(content)[0]
                    tokens = parsed.tokens
                    for index in xrange(0, len(tokens)):
                        if tokens[index].is_keyword and 'JOIN' in tokens[index].value:
                            stats[tokens[index].value] = stats.get(tokens[index].value, 0) + 1

    dump_stats(directory, 'join', stats)

def hash_stats(directory = '.'):
    stats = []

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            for query in Query.objects.filter(action = action):
                hash_count = 0
                has_explain = False
                for explain in Explain.objects.filter(query = query):
                    hash_count += len(re.findall('Hash', explain.output))
                    has_explain = True
                if has_explain:
                    stats.append(hash_count)

    dump_stats(directory, 'hash', stats)

def scan_stats(directory = '.'):
    stats = {}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            for query in Query.objects.filter(action = action):
                for explain in Explain.objects.filter(query = query):
                    for scan in re.findall('[A-Za-z][\sA-Za-z]*Scan', explain.output):
                        stats[scan] = stats.get(scan, 0) + 1

    dump_stats(directory, 'scan', stats)

def nest_stats(directory = '.'):
    stats = []

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            for query in Query.objects.filter(action = action):
                nest_count = 0
                has_explain = False
                for explain in Explain.objects.filter(query = query):
                    nest_count += len(re.findall('Nested', explain.output))
                    has_explain = True
                if has_explain:
                    stats.append(nest_count)

    dump_stats(directory, 'nest', stats)

def aggregate_stats(directory = '.'):
    stats = []

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            for query in Query.objects.filter(action = action):
                aggregate_count = 0
                has_explain = False
                for explain in Explain.objects.filter(query = query):
                    aggregate_count += len(re.findall('Aggregate', explain.output))
                    has_explain = True
                if has_explain:
                    stats.append(aggregate_count)

    dump_stats(directory, 'aggregate', stats)

def logical_stats(directory = '.'):
    stats = {}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            for query in Query.objects.filter(action = action):
                for explain in Explain.objects.filter(query = query):
                    for logical_word in ['AND', 'OR', 'ALL', 'NOT', 'ANY']:
                        stats[logical_word] = stats.get(logical_word, 0) + len(re.findall(logical_word, explain.output))

    dump_stats(directory, 'logical', stats)

def main():
    # active
    # query_stats(QUERIES_DIRECTORY)
    # coverage_stats(QUERIES_DIRECTORY)
    sort_stats(QUERIES_DIRECTORY)

    # working
    # join_stats(QUERIES_DIRECTORY)
    # scan_stats(QUERIES_DIRECTORY)
    # logical_stats(QUERIES_DIRECTORY)
    
    # deprecated
    # TODO : hash_stats(QUERIES_DIRECTORY)
    # TODO : nest_stats(QUERIES_DIRECTORY)
    # TODO : aggregate_stats(QUERIES_DIRECTORY)
        

if __name__ == '__main__':
    main()
