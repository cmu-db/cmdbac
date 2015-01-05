#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
logging.basicConfig(filename='repo_crawler.log',level=logging.DEBUG)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
#import django
#django.setup()

from crawlers import *
from crawler.models import *

if __name__ == '__main__':
    while True:
        for project_type in ProjectType.objects.all():
            crawler = GitHubCrawler(project_type)
            crawler.crawl()
            #crawler.save()
