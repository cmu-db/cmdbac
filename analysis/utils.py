# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2016-03-21 01:05:00
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2016-08-14 11:40:14
import os
import csv
import pickle

COMMITS_COUNT_THRESHOLD = 10

def filter_repository(repo):
    if repo.commits_count >= 0 and repo.commits_count <= COMMITS_COUNT_THRESHOLD:
        return True
    return False

def dump_stats(directory, description, values):
    with open(os.path.join(directory, description + '.csv'), 'wb') as csv_file:   
        writer = csv.writer(csv_file)
        writer.writerow([description])
        for label, stats in values.iteritems():
            if isinstance(stats, list):
                for i in stats:
                    writer.writerow([label, i])
            elif isinstance(stats, dict):
                for key, value in stats.iteritems():
                    if isinstance(value, list):
                        for second_value in value:
                            writer.writerow([label, key, second_value])
                    else:
                        writer.writerow([label, key, value])
            else:
                print 'can not dump {}'.format(description)

def dump_all_stats(directory, all_stats):
    for description in all_stats:
        dump_stats(directory, description, all_stats[description])

def pickle_dump(directory, description, data):
    with open(os.path.join(directory, description + '.pkl'), 'wb') as pickle_file:  
        pickle.dump(data, pickle_file)