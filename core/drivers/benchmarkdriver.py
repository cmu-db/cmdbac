import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import requests
import re
import copy
import traceback
import requests
import mechanize

from library.models import *
from cmudbac.settings import *
import utils
import extract
import submit
import count
from basedriver import BaseDriver

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## =====================================================================
## BENCHMARK DRIVER
## =====================================================================
class BenchmarkDriver(BaseDriver):
    
    def __init__(self, driver):
        BaseDriver.__init__(self, driver.deployer)
        self.forms = driver.forms
        self.browser = mechanize.Browser()
        self.browser.set_cookiejar(driver.browser._ua_handlers['_cookies'].cookiejar)
        self.browser.set_handle_robots(False)

    def submit_forms(self):
        forms_cnt = 0
        for form, browser_index in self.forms:
            try:
                if browser_index == 0:
                    part_inputs = submit.fill_form_random(self.deployer.base_path, form, self.browser)
                else:
                    part_inputs = submit.fill_form_random(self.deployer.base_path, form, None)
            except:
                pass
            forms_cnt += 1
            # LOG.info('Normal: Fill in Form on {} Successfully ...'.format(form['url']))
        return forms_cnt
