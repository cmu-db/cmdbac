import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from crawler.models import *
import utils

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()
LOG_handler = logging.StreamHandler()
LOG_formatter = logging.Formatter(fmt='%(asctime)s [%(filename)s:%(funcName)s:%(lineno)03d] %(levelname)-5s: %(message)s',
                                  datefmt='%m-%d-%Y %H:%M:%S')
LOG_handler.setFormatter(LOG_formatter)
LOG.addHandler(LOG_handler)
LOG.setLevel(logging.INFO)

## =====================================================================
## DRIVER
## =====================================================================
class Driver(object):
	
	def __init__(self):

	def drive(self):
		# get main page -- finished : get_main_page
		# recursively find all pages and extract the forms -- work on : mine.py
		# generate input for the forms and submit them	-- work on : submit.py
		