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

def tables_stats():
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
                
def main():
    tables_stats()


if __name__ == '__main__':
    main()
