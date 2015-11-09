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
	
	def __init__(self):
		self.stats = {}

	def count_transaction(self, queries):
		cnt = 0
		for query in queries:
			if query['content'].strip().lower() == 'commit':
				cnt += 1
		return cnt

	def analyze(self, queries):
		self.stats['transaction'] = self.stats.get('transaction', 0) + self.count_transaction(queries)