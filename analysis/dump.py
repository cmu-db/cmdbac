# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2016-03-21 01:05:00
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2016-03-21 01:19:27
import os
import csv
import numpy as np

NUM_BINS = 10

def dump_stats(directory, description, stats):
    if isinstance(stats, list):
        hist, bin_edges = np.histogram(stats, NUM_BINS)
        with open(os.path.join(directory, description + '.csv'), 'wb') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([description, 'nums'])
            for i in xrange(NUM_BINS):
                writer.writerow([int(bin_edges[i]), hist[i]])
    elif isinstance(stats, dict):
        with open(os.path.join(directory, description + '.csv'), 'wb') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([description, 'nums'])
            for key, value in stats.iteritems():
                writer.writerow([key, value])
    else:
        print 'can not dump {}'.format(description)

def dump_all_stats(directory, all_stats):
    for description in all_stats:
        dump_stats(directory, description, all_stats[description])
