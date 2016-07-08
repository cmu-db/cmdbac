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
        self.urls = driver.urls
        self.browser = mechanize.Browser()
        if driver.browser != None:
            self.browser.set_cookiejar(driver.browser._ua_handlers['_cookies'].cookiejar)
        self.browser.set_handle_robots(False)

    def submit_actions(self):
        actions_cnt = 0
        for form, browser_index in self.forms:
            try:
                if browser_index == 0:
                    submit.fill_form_random(self.deployer.base_path, form, self.browser)
                else:
                    submit.fill_form_random(self.deployer.base_path, form, None)
            except:
                pass
            actions_cnt += 1
        for url in self.urls:
            try:
                submit.query_url(url, self.browser)
            except:
                pass
            actions_cnt += 1
        return actions_cnt


