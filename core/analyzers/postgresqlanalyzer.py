import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import re

from baseanalyzer import BaseAnalyzer

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## =====================================================================
## MYSQL ANALYZER
## =====================================================================
class PostgreSQLAnalyzer(BaseAnalyzer):
    
    def __init__(self, deployer):
        BaseAnalyzer.__init__(self, deployer)

    def count_transaction(self, queries):
        cnt = 0
        for query in queries:
            if query['content'].strip().lower() == 'commit':
                cnt += 1
        return cnt

    def analyze_queries(self, queries):
        self.queries_stats['transaction'] = self.queries_stats.get('transaction', 0) + self.count_transaction(queries)

        try:
            conn = self.deployer.get_database_connection()
            conn.set_isolation_level(0)
            cur = conn.cursor()
            
            for query in queries:
                try:
                    content = re.search('LOG:  statement: (.+)', query['content'])
                    if content == None:
                        continue
                    content = content.group(1)
                    explain_query = 'EXPLAIN ANALYZE {};'.format(content)
                    print explain_query
                    cur.execute(explain_query)
                    rows = cur.fetchall()
                    for row in rows:
                        print row
                    print '-------------------------'
                except Exception, e:
                    LOG.exception(e)

            conn.set_isolation_level(1)
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
            cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
            self.database_stats['num_tables'] = int(cur.fetchone()[0])

            # the number of indexes
            cur.execute("SELECT COUNT(*) FROM pg_stat_all_indexes WHERE schemaname = 'public';")
            self.database_stats['num_indexes'] = int(cur.fetchone()[0])

            cur.close()
            conn.close()
        except Exception, e:
            LOG.exception(e)