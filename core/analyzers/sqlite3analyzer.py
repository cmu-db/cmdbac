import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging

from baseanalyzer import BaseAnalyzer

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

    def analyze_queries(self, queries):
        self.queries_stats['num_transactions'] = self.count_transaction(queries)

        try:
            conn = self.deployer.get_database_connection()
            cur = conn.cursor()

            for query in queries:
                try:
                    if self.is_valid_for_explain(query['raw']):
                        explain_query = 'EXPLAIN {};'.format(query['raw'])
                        # print explain_query
                        cur.execute(explain_query)
                        rows = cur.fetchall()
                        output = '\n'
                        for row in rows:
                            output += str(row) + '\n'
                        query['explain'] = output
                except Exception, e:
                    pass
                    # LOG.exception(e)

            cur.close()
            conn.close()
        except Exception, e:
            LOG.exception(e)

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