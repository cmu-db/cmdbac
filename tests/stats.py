#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *
import utils

def tables_stats():
    num_repos = 0
    stats = {}
    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        statistics = Statistic.objects.filter(attempt = repo.latest_attempt)
        if len(statistics) == 0:
            continue
        for s in statistics:
            stats[s.description] = stats.get(s.description, 0) + s.count
        num_repos += 1
    print num_repos
    print stats
    avg_stats = {}
    for key, value in stats.iteritems():
        avg_stats[key] = float(value) / num_repos
    print avg_stats

def queries_stats():
    num_queries = 0
    stats = {}
    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        forms = Form.objects.filter(attempt = repo.latest_attempt)
        for form in forms:
            counters = Counter.objects.filter(form = form)
            for counter in counters:
                stats[counter.description] = stats.get(counter.description, 0) + counter.count
                num_queries += counter.count
    print num_queries
    print stats
    avg_stats = {}
    for key, value in stats.iteritems():
        avg_stats[key] = float(value * 100) / num_queries
    print avg_stats

def coverage_stats():
    num_repos = 0
    coverage = {}
    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        forms = Form.objects.filter(attempt = repo.latest_attempt)
        covered_tables = set()
        if len(forms) == 0:
            continue
        statistics = Statistic.objects.filter(attempt = repo.latest_attempt)
        if len(statistics) == 0:
            continue
        for form in forms:
            queries = Query.objects.filter(form = form)
            for query in queries:
                m = re.search('FROM `(.*?)`', query.content)
                if m:
                    covered_tables.add(m.group(1))
        statistic = statistics.get(description = 'num_tables')
        bucket = int(float(len(covered_tables) * 100) / statistic.count / 10)
        coverage[bucket] = coverage.get(bucket, 0) + 1
    print coverage

def main():
    coverage_stats()


if __name__ == '__main__':
    main()
