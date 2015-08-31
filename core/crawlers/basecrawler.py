import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))


import time
import json
import re

from url import URL
from string import Template
from bs4 import BeautifulSoup
from datetime import datetime

from crawler.models import *

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

## CLASS