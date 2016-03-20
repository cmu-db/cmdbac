# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2016-03-21 01:05:00
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2016-03-21 01:11:53
import os
import csv
import numpy as np

NUM_BINS = 10

def dump_stats(directory, stats):
    for description in stats:
        if isinstance(stats[description], list):
            hist, bin_edges = np.histogram(stats[description], NUM_BINS)
            with open(os.path.join(directory, description + '.csv'), 'wb') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow([description, 'nums'])
                for i in xrange(NUM_BINS):
                    writer.writerow([int(bin_edges[i]), hist[i]])
        elif isinstance(stats[description], dict):
            with open(os.path.join(directory, description + '.csv'), 'wb') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow([description, 'nums'])
                for key, value in stats[description].iteritems():
                    writer.writerow([key, value])
        else:
            print 'can not dump {}'.format(description)