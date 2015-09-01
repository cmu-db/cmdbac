#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "core"))

import time
import traceback
import logging
logging.basicConfig(filename='repo_crawler.log',level=logging.DEBUG)
import requests
from requests.auth import HTTPBasicAuth

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
import django
django.setup()

import crawlers
from crawler.models import *

if __name__ == '__main__':

    requests.get('https://api.github.com/user', auth=HTTPBasicAuth('zeyuanxy', 'wazy41871314'))
    
    while True:
        for cs in CrawlerStatus.objects.all():
            repo_source = cs.source
            project_type = cs.project_type

            moduleName = "crawlers.%s" % (repo_source.crawler_class.lower())
            moduleHandle = __import__(moduleName, globals(), locals(), [repo_source.crawler_class])
            klass = getattr(moduleHandle, repo_source.crawler_class)
            crawler = klass(cs)

            try:
                crawler.crawl()
            except:
                print traceback.print_exc()
                pass
            time.sleep(60)
            #crawler.save()
        ## FOR
    ## WHILE
## IF
