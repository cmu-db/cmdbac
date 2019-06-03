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
        self.database_informations = {}
        self.deployer = deployer

    def is_valid_for_explain(self, query):
        if not query:
            return False
        prefixes = ['show', 'begin', 'end', 'commit', 'set']
        lowered_query = query.lower()
        if any(lowered_query.startswith(prefix) for prefix in prefixes):
            return False
        return True

    def count_transaction(self, queries):
        transaction = False
        transaction_count = 0
        for query in queries:
            if 'BEGIN' in query['content'].upper() or 'START TRANSACTION' in query['content'].upper():
                transaction = True
            elif transaction:
                if 'COMMIT' in query['content'].upper():
                    # for each transaction, count the number of transactions
                    transaction_count += 1
                    transaction = False
        return transaction_count

    def analyze_queries(self, queries):
        raise NotImplementedError("Unimplemented %s" % self.__init__.__self__.__class__)

    def analyze_database(self):
        raise NotImplementedError("Unimplemented %s" % self.__init__.__self__.__class__)