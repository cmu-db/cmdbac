#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import re
import csv
import numpy as np

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *

NUM_BINS = 10

def table_stats():
    stats = {}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        statistics = Statistic.objects.filter(attempt = repo.latest_attempt)
        if len(statistics) == 0:
            continue
        
        for s in statistics:
            if s.description == 'num_transactions':
                continue
            if s.description not in stats:
                stats[s.description] = []
            stats[s.description].append(s.count)
    
    for description in stats:
        hist, bin_edges = np.histogram(stats[description], NUM_BINS)
        
        with open(os.path.join(directory, description + '.csv'), 'wb') as csv_file:
            writer = csv.writer(csv_file)
            for i in xrange(NUM_BINS):
                writer.writerow([int(bin_edges[i]), hist[i]])

def column_stats():
    stats = {'nullable': {}, 'types': {}}

    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        informations = Information.objects.filter(attempt = repo.latest_attempt)
        if len(informations) == 0:
            continue

        for i in informations:
            if i.name == 'columns':
                if repo.latest_attempt.database.name == 'PostgreSQL':
                    for column in re.findall('(\(.*?\))[,\]]', i.description):
                        cells = column.split(',')
                        
                        nullable = str(cells[6]).replace("'", "").strip()
                        stats['nullable'][nullable] = stats['nullable'].get(nullable, 0) + 1

                        _type = str(cells[7]).replace("'", "").strip()
                        stats['types'][_type] = stats['types'].get(_type, 0) + 1


    print stats

def main():
    # table_stats()
    column_stats()

if __name__ == '__main__':
    main()
