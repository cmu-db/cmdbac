#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
logging.basicConfig(filename='repo_crawler.log',level=logging.DEBUG)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
#import django
#django.setup()

import crawlers
from crawler.models import *

if __name__ == '__main__':
    
    for cs in CrawlerStatus.objects.all():
        repo_source = cs.source
        project_type = cs.project_type

        moduleName = "crawlers.%s" % (repo_source.crawler_class.lower())
        moduleHandle = __import__(moduleName, globals(), locals(), [repo_source.crawler_class])
        klass = getattr(moduleHandle, repo_source.crawler_class)

        crawler = klass(cs)
        crawler.crawl()
        
        break
        #crawler.save()
    ## FOR
## IF
