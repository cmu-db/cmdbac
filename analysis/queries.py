#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

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
    stats = {}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        actions = Action.objects.filter(attempt = repo.latest_attempt)
        if len(actions) == 0:
            continue
        
        for action in actions:
            counters = Counter.objects.filter(action = action)
            for counter in counters:
                stats[counter.description] = stats.get(counter.description, 0) + counter.count

    dump_stats(directory, 'query', stats)

def table_coverage_stats(directory = '.'):
    stats = []

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
        
        covered_tables = set()
        for action in actions:
            for query in Query.objects.filter(action = action):
                for table in re.findall('FROM\s*\S+', query.content.upper()):
                    table_name = table.replace('FROM', '').replace("'", "").replace(' ', '')
                    covered_tables.add(table_name)

        percentage = int(float(len(covered_tables) * 100) / table_count)
        percentage = min(percentage, 100)
        stats.append(percentage)

    dump_stats(directory, 'table_coverage', stats)
        
def column_coverage_stats(directory = '.'):
    stats = []

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        actions = Action.objects.filter(attempt = repo.latest_attempt)
        if len(actions) == 0:
            continue

        informations = Information.objects.filter(attempt = repo.latest_attempt).filter(name = 'columns')
        if len(informations) == 0:
            continue
        information = informations[0]
        column_count = 0
        if repo.latest_attempt.database.name == 'PostgreSQL':
            column_count = len(re.findall('(\(.*?\))[,\]]', information.description))
        elif repo.latest_attempt.database.name == 'MySQL':
            column_count = len(re.findall('(\(.*?\))[,\)]', information.description))
        if column_count == 0:
            continue
        
        covered_columns = set()
        for action in actions:
            for query in Query.objects.filter(action = action):
                parsed = sqlparse.parse(query.content)[0]
                tokens = parsed.tokens
                for token in tokens:
                    if isinstance(token, sqlparse.sql.Identifier):
                        covered_columns.add(token.value)
        percentage = int(float(len(covered_columns) * 100) / column_count)
        percentage = min(percentage, 100)
        stats.append(percentage)

    dump_stats(directory, 'column_coverage', stats)

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

def index_coverage_stats(directory = '.'):
    stats = []

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        actions = Action.objects.filter(attempt = repo.latest_attempt)
        if len(actions) == 0:
            continue

        statistics = Statistic.objects.filter(attempt = repo.latest_attempt).filter(description = 'num_indexes')
        if len(statistics) == 0:
            continue
        index_count = statistics[0].count
        if index_count == 0:
            continue
        
        covered_indexes = set()
        for action in actions:
            for query in Query.objects.filter(action = action):
                for explain in Explain.objects.filter(query = query):
                    for raw_index in re.findall('Index.*?Scan.*?on \S+', explain.output):
                        index = raw_index.split()[-1]
                        covered_indexes.add(index)
               
        percentage = int(float(len(covered_indexes) * 100) / index_count)
        percentage = min(percentage, 100)
        stats.append(percentage)

    dump_stats(directory, 'index_coverage', stats)

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

def sort_stats(directory = '.'):
    stats = {'sort_methods': {}, 'sort_keys': {}}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            for query in Query.objects.filter(action = action):
                for explain in Explain.objects.filter(query = query):
                    for raw_sort_method in re.findall('Sort Method: \S+', explain.output):
                        sort_method = raw_sort_method.split()[-1]
                        stats['sort_methods'][sort_method] = stats['sort_methods'].get(sort_method, 0) + 1
                    for sort_keys in re.findall('Sort Key: .*', explain.output):
                        sort_keys_count = len(re.findall(',', sort_keys)) + 1
                        stats['sort_keys'][sort_keys_count] = stats['sort_keys'].get(sort_keys_count, 0) + 1

    dump_all_stats(directory, stats)

def step_stats(directory = '.'):
    stats = []

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        if repo.latest_attempt.database.name == 'MySQL':
            continue

        for action in Action.objects.filter(attempt = repo.latest_attempt):
            for query in Query.objects.filter(action = action):
                step_count = 0
                has_explain = False
                for explain in Explain.objects.filter(query = query):
                    step_count += 1 + len(re.findall('->', explain.output))
                    has_explain = True
                if has_explain:
                    stats.append(step_count)

    dump_stats(directory, 'step', stats)


def main():
    # query_stats(QUERIES_DIRECTORY)
    # join_stats(QUERIES_DIRECTORY)
    # scan_stats(QUERIES_DIRECTORY)

    table_coverage_stats(QUERIES_DIRECTORY)
    column_coverage_stats(QUERIES_DIRECTORY)
    index_coverage_stats(QUERIES_DIRECTORY)
    logical_stats(QUERIES_DIRECTORY)
    sort_stats(QUERIES_DIRECTORY)
    step_stats(QUERIES_DIRECTORY)


    # TODO : hash_stats(QUERIES_DIRECTORY)
    # TODO : nest_stats(QUERIES_DIRECTORY)
    # TODO : aggregate_stats(QUERIES_DIRECTORY)
        

if __name__ == '__main__':
    main()
