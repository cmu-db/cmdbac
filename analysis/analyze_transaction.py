#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import re
import csv
from utils import filter_repository, dump_all_stats

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *

TRANSACTION_DIRECTORY = 'transactions'

def action_stats(directory = '.'):
    stats = {'action_query_count': {}}

    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        if filter_repository(repo):
            continue

        project_type_name = repo.project_type.name
        if project_type_name not in stats['action_query_count']:
            stats['action_query_count'][project_type_name] = []
        
        for action in Action.objects.filter(attempt = repo.latest_successful_attempt):
            query_count = len(Query.objects.filter(action = action))
            if query_count > 0:
                stats['action_query_count'][project_type_name].append(query_count)

            
    dump_all_stats(directory, stats)

def transaction_stats(directory = '.'):
    stats = {'transaction_count': {}, 'transaction_query_count': {}, 'transaction_read_count': {}, 'transaction_write_count': {}}

    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        if filter_repository(repo):
            continue
        
        project_type_name = repo.project_type.name
        if project_type_name not in stats['transaction_count']:
            stats['transaction_count'][project_type_name] = []
        if project_type_name not in stats['transaction_query_count']:
            stats['transaction_query_count'][project_type_name] = []
        if project_type_name not in stats['transaction_read_count']:
            stats['transaction_read_count'][project_type_name] = []
        if project_type_name not in stats['transaction_write_count']:
            stats['transaction_write_count'][project_type_name] = []
        

        for action in Action.objects.filter(attempt = repo.latest_successful_attempt):
            transaction = ''
            query_count = 0
            transaction_count = 0

            for query in Query.objects.filter(action = action):
                if 'BEGIN' in query.content.upper() or 'START TRANSACTION' in query.content.upper():
                    transaction = query.content + '\n'
                    query_count = 1
                elif transaction != '':
                    transaction += query.content + '\n'
                    query_count += 1
                    if 'COMMIT' in query.content.upper():
                        transaction = transaction.strip('\n')
                    
                        # for each transaction, count the number of transactions
                        transaction_count += 1

                        # for each transaction, count the number of read/write
                        read_count = len(re.findall('SELECT', transaction.upper()))
                        stats['transaction_read_count'][project_type_name].append(read_count)
                        write_count = 0
                        for keyword in ['INSERT', 'DELETE', 'UPDATE']:
                            write_count += len(re.findall(keyword, transaction.upper()))
                        stats['transaction_write_count'][project_type_name].append(write_count)
                        
                        # for each transaction, count the queries
                        query_count -= 2
                        stats['transaction_query_count'][project_type_name].append(query_count)

                        transaction = ''

            if transaction_count > 0:
                stats['transaction_count'][project_type_name].append(transaction_count)

            
    dump_all_stats(directory, stats)

def add_transaction_stat(directory = '.'):
    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        if filter_repository(repo):
            continue
        
        transaction_count = 0
        for action in Action.objects.filter(attempt = repo.latest_successful_attempt):
            transaction = False

            for query in Query.objects.filter(action = action):
                if 'BEGIN' in query.content.upper() or 'START TRANSACTION' in query.content.upper():
                    transaction = True
                elif transaction:
                    if 'COMMIT' in query.content.upper():
                        # for each transaction, count the number of transactions
                        transaction_count += 1
                        transaction = False

        statistic = Statistic()
        statistic.description = 'num_transactions'
        statistic.count = transaction_count
        statistic.attempt = repo.latest_successful_attempt
        statistic.save()  

def main():
    # active
    # action_stats(TRANSACTION_DIRECTORY)
    # transaction_stats(TRANSACTION_DIRECTORY)
    add_transaction_stat()
    
    # working
    
    # deprecated
if __name__ == '__main__':
    main()
