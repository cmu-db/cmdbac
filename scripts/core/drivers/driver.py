import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging

from crawler.models import *
import utils

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================

## =====================================================================
## DRIVER
## =====================================================================
class Driver(object):
	
	def __init__(self):
		pass
	
	def drive(self, deployer):
		main_page = deployer.get_main_page()
		print main_page

		print utils.run_command('cd {} && {}'.format(
			os.path.join(os.path.dirname(__file__), 'scrapy'),
			'scrapy crawl form -a start_url="{}"').format(main_page))
		# recursively find all pages and extract the forms -- work on : mine.py
		# generate input for the forms and submit them	-- work on : submit.py
		