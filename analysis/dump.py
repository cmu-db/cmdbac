# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2016-03-21 01:05:00
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2016-03-28 23:48:09
import os
import csv

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
                    writer.writerow([label, key, value])
            else:
                print 'can not dump {}'.format(description)

def dump_all_stats(directory, all_stats):
    for description in all_stats:
        dump_stats(directory, description, all_stats[description])
