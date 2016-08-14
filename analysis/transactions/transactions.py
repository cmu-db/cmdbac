# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2016-08-14 11:12:48
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2016-08-14 20:40:19
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import pickle
import sqlparse

from utils import dump_all_stats

def analyze_blind_write():
    total = 0
    count = 0
    stats = {'transaction_count': {}, 'blind_write_count': {}}

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

            for i in xrange(len(queries)):
                if is_write(queries[i]):
                    writes.append((i, queries[i]))

            is_blind_write = False
            index, other_index = -1, -1
            if len(writes) > 1:
                identifiers = [(i, get_identifiers(sqlparse.parse(query))) for (i, query) in writes]
                for i in xrange(1, len(identifiers)):
                    if is_blind_write:
                        break

                    for j in xrange(i):
                        if is_blind_write:
                            break

                        index, identifier = identifiers[i]
                        other_index, other_identifier = identifiers[j]
                        if identifier.intersection(other_identifier):
                            is_blind_write = True
                            for k in xrange(other_index + 1, index):
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
                print repo_name, project_type
                print queries[index]
                print queries[other_index]
                print '+' * 10
                print transaction.encode('utf-8')
                print '-' * 20

            stats['transaction_count'][project_type] = [stats['transaction_count'].get(project_type, [0])[0] + 1]
                
    total = len(transactions)

    print stats

    print 'Total # of Transactions:', total
    print 'Total # of Blind Writes:', count

    dump_all_stats('.', stats)

def main():
    analyze_blind_write()
    # pattern()

if __name__ == '__main__':
    main()