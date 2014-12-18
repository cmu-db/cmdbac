#!/usr/bin/env python

import os
import logging
from crawler_class import Crawler
logging.basicConfig(filename='repo_crawler.log',level=logging.DEBUG)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

import django
django.setup()


from crawler.models import *

if __name__ == '__main__':
    while True:
        repo_types = Type.objects.all()

        for repo_type in repo_types:
            crawler = Crawler(repo_type)
            crawler.crawl()
            crawler.save()
