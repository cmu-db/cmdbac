import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from baseanalyzer import BaseAnalyzer

import logging

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## =====================================================================
## SQLITE3 ANALYZER
## =====================================================================
class SQLite3Analyzer(BaseAnalyzer):
    
    def __init__(self, deployer):
        BaseAnalyzer.__init__(self, deployer)

    def count_transaction(self, queries):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)

    def analyze_queries(self, queries):
        raise NotImplementedError("Unimplemented %s" % self.__init__.im_class)

    def analyze_database(self):
        try:
            conn = self.deployer.get_database_connection()
            cur = conn.cursor()
            database = self.deployer.get_database_name()
            
            # the number of tables
            cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table';")
            self.database_stats['num_tables'] = int(cur.fetchone()[0])

            # the number of indexes
            cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'index';")
            self.database_stats['num_indexes'] = int(cur.fetchone()[0])

            cur.close()
            conn.close()
        except Exception, e:
            LOG.exception(e)