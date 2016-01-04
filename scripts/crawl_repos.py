#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import time
import logging
logging.basicConfig(filename='repo_crawler.log',level=logging.DEBUG)
import json
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

import crawlers
from library.models import *

if __name__ == '__main__':
    try:
        with open(os.path.join(os.path.dirname(__file__), os.pardir, "secrets", "secrets.json"), 'r') as auth_file:
            auth = json.load(auth_file)
    except:
        auth = None

    while True:
        cs = CrawlerStatus.objects.get(id = 4)
        repo_source = cs.source
        project_type = cs.project_type

        moduleName = "crawlers.%s" % (repo_source.crawler_class.lower())
        moduleHandle = __import__(moduleName, globals(), locals(), [repo_source.crawler_class])
        klass = getattr(moduleHandle, repo_source.crawler_class)
        crawler = klass(cs, auth)

        try:
            crawler.crawl()
        except:
            print traceback.print_exc()
        time.sleep(10)
    ## WHILE
## IF
