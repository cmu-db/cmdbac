import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

from crawler.models import *

class BaseCrawler(object):
    def __init__(self, crawlerStatus, auth):
        self.crawlerStatus = crawlerStatus
        self.auth = auth
    # DEF
        
    def search(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    # DEF
    
    def crawl(self):
        nextResults = self.search()
    ## DEF

## CLASS