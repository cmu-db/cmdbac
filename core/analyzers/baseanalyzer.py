import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## =====================================================================
## BASE ANALYZER
## =====================================================================
class BaseAnalyzer(object):
    
    def __init__(self, deployer):
        self.queries_stats = {}
        self.database_stats = {}
        self.deployer = deployer
    
    def analyze_queries(self, queries):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)

    def analyze_database(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)