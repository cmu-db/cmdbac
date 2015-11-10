import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import requests
import re
import copy
import traceback
import mechanize

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
    
    def __init__(self, deployer, driver = None):
        Driver.__init__(self, deployer)
        if driver != None:
            self.forms = driver.forms
            if driver.browser != None:
                self.browser = mechanize.Browser()
                self.browser.set_cookiejar(driver.browser._ua_handlers['_cookies'].cookiejar)
            else:
                self.browser = None

    def submit_forms(self):
        forms_cnt = 0
        for form, browser_index in self.forms:
            if browser_index == 0:
                part_inputs = submit.fill_form_random(self.deployer.base_path, form, self.browser)
            else:
                part_inputs = submit.fill_form_random(self.deployer.base_path, form, None)
            forms_cnt += 1
            # LOG.info('Normal: Fill in Form on {} Successfully ...'.format(form['url']))
        return forms_cnt
