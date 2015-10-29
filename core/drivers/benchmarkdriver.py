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

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## =====================================================================
## DRIVER
## =====================================================================
class BenchmarkDriver(Driver):
    
    def __init__(self):
        pass

    def submit_forms(self, deployer):
        # get main page
        main_url = deployer.get_main_url()

        for form in self.forms:
            try:
                part_inputs = submit.fill_form_random(deployer.base_path, form, self.browser)
            except:
                traceback.print_exc()
                part_inputs = None
            if part_inputs == None or if len(form['queries']) == 0:
                continue
            # LOG.info('Normal: Fill in Form on {} Successfully ...'.format(form['url']))
