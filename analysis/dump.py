# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2016-03-21 01:05:00
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2016-03-28 00:30:15
import os
import csv

def dump_stats(directory, description, values, with_labels = False):
    with open(os.path.join(directory, description + '.csv'), 'wb') as csv_file:   
        writer = csv.writer(csv_file)
        writer.writerow([description])
        if with_labels:
            for label, stats in values.iteritems():
                if isinstance(stats, list):
                    for i in stats:
                        writer.writerow([label, i])
                else:
                    print 'can not dump {}'.format(description)
        else:
            if isinstance(values, dict):
                for key, value in values.iteritems():
                    writer.writerow([key, value])
            else:
                print 'can not dump {}'.format(description)

def dump_all_stats(directory, all_stats, with_labels = False):
    for description in all_stats:
        dump_stats(directory, description, all_stats[description], with_labels)
