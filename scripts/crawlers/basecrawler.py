import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import time
import json
import re

from url import URL
from utils import Utils
from string import Template
from bs4 import BeautifulSoup
from datetime import datetime

from constants import Constants
from crawler.models import *

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
#import django
#django.setup()

class BaseCrawler(object):
    def __init__(self, crawlerStatus):
        self.crawlerStatus = crawlerStatus
    # DEF
        
    def search(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    # DEF
    
    def crawl(self):
        # For now let's do it once...
        nextResults = self.search()
    ## DEF
        
    #def save(self):
        #repo_type = Type.objects.get(name=self.name)
        #repo_type.cur_size = self.cur_size
        #repo_type.save()

## CLASS