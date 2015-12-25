import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

from library.models import *

class BaseCrawler(object):
    def __init__(self, crawlerStatus, auth = None):
        self.crawlerStatus = crawlerStatus
        self.auth = auth
    # DEF
        
    def search(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    # DEF
    
    def crawl(self):
        nextResults = self.search()
    ## DEF

    def add_repository(self, name, setup_scripts):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    # DEF

    def download_repository(self, repo_name, zip_name):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)
    # DEF

## CLASS