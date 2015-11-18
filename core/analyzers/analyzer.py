import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## =====================================================================
## ANALYZER
## =====================================================================
class Analyzer(object):
    
    def __init__(self, deployer):
        self.queries_stats = {}
        self.database_stats = {}
        self.deployer = deployer

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
            cur = conn.cursor()

            for query in queries:
                try:
                    explain_query = 'explain {};'.format(query['content'])
                    print explain_query
                    cur.execute(explain_query)
                    rows = cur.fetchall()
                    for row in rows:
                        print row
                    print '-------------------------'
                except Exception, e:
                    LOG.exception(e)

        except Exception, e:
            LOG.exception(e)

    def analyze_database(self):
        try:
            conn = self.deployer.get_database_connection()
            cur = conn.cursor()
            database = self.deployer.get_database_name()
            
            # the number of tables
            cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '{}';".format(database))
            self.database_stats['num_tables'] = int(cur.fetchone()[0])

            # the number of indexes
            cur.execute("SELECT COUNT(DISTINCT table_name, index_name) FROM information_schema.statistics WHERE table_schema = '{}';".format(database))
            self.database_stats['num_indexes'] = int(cur.fetchone()[0])

            # the number of constraints
            cur.execute("SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema = '{}';".format(database))
            self.database_stats['num_constraints'] = int(cur.fetchone()[0])

            # the number of foreign keys
            cur.execute("SELECT COUNT(*) FROM information_schema.referential_constraints WHERE constraint_schema = '{}';".format(database))
            self.database_stats['num_foreignkeys'] = int(cur.fetchone()[0])

            cur.close()
            conn.close()
        except Exception, e:
            LOG.exception(e)