#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
logging.basicConfig(filename='repo_crawler.log',level=logging.DEBUG)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
#import django
#django.setup()

from repo_crawlers import GitHubCrawler
from crawler.models import *

if __name__ == '__main__':
    while True:
        repo_types = Type.objects.all()

        for repo_type in repo_types:
            crawler = GitHubCrawler(repo_type)
            crawler.crawl()
            crawler.save()
