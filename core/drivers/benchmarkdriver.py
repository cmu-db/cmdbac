import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import requests
import re
import copy
import traceback

from crawler.models import *
from db_webcrawler.settings import *
import utils
import extract
import submit
import count
from driver import Driver

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## =====================================================================
## DRIVER
## =====================================================================
class BenchmarkDriver(Driver):
    
    def __init__(self, deployer):
        Driver.__init__(self, deployer)

    def submit_forms(self):
        for form in self.forms:
            try:
                part_inputs = submit.fill_form_random(self.deployer.base_path, form, self.browser)
            except:
                traceback.print_exc()
                part_inputs = None
            # LOG.info('Normal: Fill in Form on {} Successfully ...'.format(form['url']))
