import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import re

from .baseanalyzer import BaseAnalyzer

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## =====================================================================
## POSTGRESQL ANALYZER
## =====================================================================
class PostgreSQLAnalyzer(BaseAnalyzer):

    def __init__(self, deployer):
        BaseAnalyzer.__init__(self, deployer)

    def analyze_queries(self, queries):
        self.queries_stats['num_transactions'] = self.count_transaction(queries) + self.queries_stats.get('num_transactions', 0)

        try:
            conn = self.deployer.get_database_connection()
            conn.set_isolation_level(0)
            cur = conn.cursor()

            for query in queries:
                try:
                    if self.is_valid_for_explain(query['raw']):
                        explain_query = 'EXPLAIN ANALYZE {};'.format(query['raw'])
                        # print explain_query
                        cur.execute(explain_query)
                        rows = cur.fetchall()
                        output = '\n'
                        for row in rows:
                            output += row[0] + '\n'
                        query['explain'] = output
                except Exception as e:
                    pass
                    # LOG.exception(e)

            conn.set_isolation_level(1)
            cur.close()
            conn.close()
        except Exception as e:
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

            # the number of constraints
            cur.execute("SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema = 'public';")
            self.database_stats['num_constraints'] = int(cur.fetchone()[0])

            # the number of foreign keys
            cur.execute("SELECT COUNT(*) FROM information_schema.referential_constraints WHERE constraint_schema = 'public';")
            self.database_stats['num_foreignkeys'] = int(cur.fetchone()[0])

            # the full information of tables
            cur.execute("SELECT * FROM information_schema.tables WHERE table_schema = 'public';")
            self.database_informations['tables'] = str(cur.fetchall())

            # the full information of columns
            cur.execute("SELECT * FROM information_schema.columns WHERE table_schema = 'public';")
            self.database_informations['columns'] = str(cur.fetchall())

            # the full information of indexes
            cur.execute("SELECT * FROM pg_stat_all_indexes WHERE schemaname = 'public';")
            self.database_informations['indexes'] = str(cur.fetchall())

            # the full information of constraints
            cur.execute("SELECT * FROM information_schema.table_constraints WHERE constraint_schema = 'public';")
            self.database_informations['constraints'] = str(cur.fetchall())

            # the full information of constraints
            cur.execute("SELECT * FROM information_schema.key_column_usage WHERE constraint_schema = 'public';")
            self.database_informations['key_column_usage'] = str(cur.fetchall())

            # the full information of foreign keys
            cur.execute("SELECT * FROM information_schema.referential_constraints WHERE constraint_schema = 'public';")
            self.database_informations['foreignkeys'] = str(cur.fetchall())

            # the full information of triggers
            cur.execute("SELECT * FROM information_schema.triggers WHERE trigger_schema = 'public';")
            self.database_informations['triggers'] = str(cur.fetchall())

            # the full information of views
            cur.execute("SELECT * FROM information_schema.views WHERE table_schema = 'public';")
            self.database_informations['views'] = str(cur.fetchall())

            cur.close()
            conn.close()
        except Exception as e:
            LOG.exception(e)