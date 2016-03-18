#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import re
import csv
import numpy as np
import sqlparse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *

NUM_BINS = 10

def query_stats():
    stats = {}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        actions = Action.objects.filter(attempt = repo.latest_attempt)
        if len(actions) == 0:
            continue
        
        for action in actions:
            counters = Counter.objects.filter(action = action)
            for counter in counters:
                stats[counter.description] = stats.get(counter.description, 0) + counter.count
                stats['TOTAL'] = stats.get('TOTAL', 0) + counter.count

    print stats

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
        
        covered_tables = set()
        for action in actions:
            for query in Query.objects.filter(action = action):
                for table in re.findall('FROM\s*\S+', query.content.upper()):
                    table_name = table.replace('FROM', '').replace("'", "").replace(' ', '')
                    covered_tables.add(table_name)
               
        percentage = int(float(len(covered_tables) * 100) / table_count)
        stats.append(percentage)

    hist, bin_edges = np.histogram(stats, NUM_BINS)
        
    with open(os.path.join(directory, 'table_coverage.csv'), 'wb') as csv_file:
        writer = csv.writer(csv_file)
        for i in xrange(NUM_BINS):
            writer.writerow([int(bin_edges[i]), hist[i]])

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
        
        covered_columns = set()
        for action in actions:
            for query in Query.objects.filter(action = action):
                parsed = sqlparse.parse(query.content)[0]
                tokens = parsed.tokens
                for token in tokens:
                    if isinstance(token, sqlparse.sql.Identifier):
                        covered_columns.add(token.value)
               
        percentage = int(float(len(covered_columns) * 100) / column_count)
        stats.append(percentage)

    hist, bin_edges = np.histogram(stats, NUM_BINS)
        
    with open(os.path.join(directory, 'column_coverage.csv'), 'wb') as csv_file:
        writer = csv.writer(csv_file)
        for i in xrange(NUM_BINS):
            writer.writerow([int(bin_edges[i]), hist[i]])

def join_stats():
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

    print stats

def hash_stats(directory = '.'):
    stats = []

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        hash_count = 0
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            for query in Query.objects.filter(action = action):
                for explain in Explain.objects.filter(query = query):
                    hash_count += len(re.findall('Hash', explain.output))
        stats.append(hash_count)

    hist, bin_edges = np.histogram(stats, NUM_BINS)
        
    with open(os.path.join(directory, 'hash_stats.csv'), 'wb') as csv_file:
        writer = csv.writer(csv_file)
        for i in xrange(NUM_BINS):
            writer.writerow([int(bin_edges[i]), hist[i]])

def scan_stats():
    stats = {}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            for query in Query.objects.filter(action = action):
                for explain in Explain.objects.filter(query = query):
                    for scan in re.findall('[A-Za-z][\sA-Za-z]*Scan', explain.output):
                        stats[scan] = stats.get(scan, 0) + 1

    print stats

def nest_stats(directory = '.'):
    stats = []

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        nest_count = 0
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            for query in Query.objects.filter(action = action):
                for explain in Explain.objects.filter(query = query):
                    nest_count += len(re.findall('Nested', explain.output))
        stats.append(nest_count)

    hist, bin_edges = np.histogram(stats, NUM_BINS)
        
    with open(os.path.join(directory, 'nest_stats.csv'), 'wb') as csv_file:
        writer = csv.writer(csv_file)
        for i in xrange(NUM_BINS):
            writer.writerow([int(bin_edges[i]), hist[i]])

def main():
    # query_stats()
    # table_coverage_stats()
    # column_coverage_stats()
    # join_stats()
    # hash_stats()
    # scan_stats()
    nest_stats()

if __name__ == '__main__':
    main()