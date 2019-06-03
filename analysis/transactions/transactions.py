# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2016-08-14 11:12:48
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2016-11-02 00:45:48
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import pickle
import sqlparse

from utils import dump_all_stats

def count_transaction():
    stats = {'transaction_count': {}}

    with open('transactions.pkl', 'rb') as pickle_file:
        transactions = pickle.load(pickle_file)

        for repo_name, project_type, transaction in transactions:
            stats['transaction_count'][project_type] = [stats['transaction_count'].get(project_type, [0])[0] + 1]

    print(stats)

    dump_all_stats('.', stats)

def blind_write():
    total = 0
    count = 0
    stats = {'blind_write_count': {}}

    def is_write(query):
        return ('INSERT' in query or 'UPDATE' in query) and ('UTC LOG:  ' not in query)

    def get_identifiers(parsed):
        identifiers = []
        for token in parsed[0].tokens:
            if isinstance(token, sqlparse.sql.Identifier):
                identifiers.append(token.value)

        return set(identifiers)

    def is_read_by(identifier, query):
        if 'SELECT' not in query:
            return False
        other_identifier = get_identifiers(sqlparse.parse(query))
        return identifier.intersection(other_identifier)

    with open('transactions.pkl', 'rb') as pickle_file:
        transactions = pickle.load(pickle_file)

        for repo_name, project_type, transaction in transactions:
            queries = transaction.split('\n')
            writes = []

            for i in range(len(queries)):
                if is_write(queries[i]):
                    writes.append((i, queries[i]))

            is_blind_write = False
            index, other_index = -1, -1
            if len(writes) > 1:
                identifiers = [(i, get_identifiers(sqlparse.parse(query))) for (i, query) in writes]
                for i in range(1, len(identifiers)):
                    if is_blind_write:
                        break

                    for j in range(i):
                        if is_blind_write:
                            break

                        index, identifier = identifiers[i]
                        other_index, other_identifier = identifiers[j]
                        if identifier.intersection(other_identifier):
                            is_blind_write = True
                            for k in range(other_index + 1, index):
                                if is_read_by(identifier, queries[k]):
                                    is_blind_write = False
                                    break

                            if is_blind_write:
                                count += 1
                                stats['blind_write_count'][project_type] = [stats['blind_write_count'].get(project_type, [0])[0] + 1]
                                # for k in xrange(other_index + 1, index):
                                #    print 1, queries[k]
                                # print
                                # raw_input()

            if is_blind_write:
                print(repo_name, project_type)
                print(queries[index])
                print(queries[other_index])
                print('+' * 10)
                print(transaction.encode('utf-8'))
                print('-' * 20)

    print(stats)

    print('Total # of Blind Writes:', count)

    dump_all_stats('.', stats)

def empty_transaction():
    stats = {'empty_transaction_count': {}, 'empty_pattern_count': {}}

    with open('transactions.pkl', 'rb') as pickle_file:
        transactions = pickle.load(pickle_file)

        for repo_name, project_type, transaction in transactions:
            queries = transaction.split('\n')

            if project_type not in stats['empty_pattern']:
                stats['empty_pattern'][project_type] = {}

            if len(queries) == 2:
                stats['empty_transaction_count'][project_type] = [stats['empty_transaction_count'].get(project_type, [0])[0] + 1]

                if 'BEGIN' in queries[0].upper():
                    stats['empty_pattern_count'][project_type]['BEGIN'] = stats['empty_pattern_count'][project_type].get('BEGIN', 0) + 1
                elif 'AUTOCOMMIT' in queries[0].upper():
                    stats['empty_pattern_count'][project_type]['AUTOCOMMIT'] = stats['empty_pattern_count'][project_type].get('AUTOCOMMIT', 0) + 1

    print(stats)

    dump_all_stats('.', stats)

def pattern():
    stats = {'pattern_count': {}}

    with open('transactions.pkl', 'rb') as pickle_file:
        transactions = pickle.load(pickle_file)

        for repo_name, project_type, transaction in transactions:
            queries = transaction.split('\n')

            if project_type not in stats['pattern_count']:
                stats['pattern_count'][project_type] = {}

            if 'BEGIN' in queries[0].upper():
                stats['pattern_count'][project_type]['BEGIN'] = stats['pattern_count'][project_type].get('BEGIN', 0) + 1
            elif 'AUTOCOMMIT' in queries[0].upper():
                stats['pattern_count'][project_type]['AUTOCOMMIT'] = stats['pattern_count'][project_type].get('AUTOCOMMIT', 0) + 1

    print(stats)

    dump_all_stats('.', stats)

def state_machine_analysis():
    state_machines = {}

    def find_query_type(query):
        for query_type in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']:
            if query_type in query:
                return query_type[0]
        return None

    with open('transactions.pkl', 'rb') as pickle_file:
        transactions = pickle.load(pickle_file)

        for repo_name, project_type, transaction in transactions:
            queries = transaction.split('\n')
            queries = [query for query in queries if 'COMMIT' not in query.upper()]
            states = list(map(find_query_type, queries))
            states = [x for x in states if x != None]
            if states:
                states_str = ''.join(states)
                state_machines[states_str] = state_machines.get(states_str, 0) + 1

        print(sorted(iter(state_machines.items()), key = lambda x_y: x_y[1], reverse = True)[:10])


def main():
    # count_transaction()
    # blind_write()
    # empty_transaction()
    # pattern()
    state_machine_analysis()

if __name__ == '__main__':
    main()