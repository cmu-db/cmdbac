#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *
import utils

def main():
    num_repos = 0
    stats = {}
    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        statistic = Statistic.objects.filter(attempt = repo.latest_attempt)
        if len(statistic) != 0:
            for s in statistic:
                stats[s.description] = stats.get(s.description, 0) + s.count
            num_repos += 1
    print num_repos
    print stats
    avg_stats = {}
    for key, value in stats.iteritems():
        avg_stats[key] = float(value) / num_repos
    print avg_stats


if __name__ == '__main__':
    main()
