import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import requests
import re
import traceback
import requests
import mechanize
import random

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

MAX_RANDOM_WALK_DEPTH = 3
MAX_RANDOM_WALK_COUNT = 100

## =====================================================================
## RANDOM DRIVER
## =====================================================================
class RandomDriver(BaseDriver):

    def __init__(self, driver):
        BaseDriver.__init__(self, driver.deployer)
        self.forms = driver.forms
        self.urls = driver.urls
        if driver.browser != None:
            self.cookiejar = driver.browser._ua_handlers['_cookies'].cookiejar
        self.walked_path = set()

    def new_browser(self, cookiejar = None, url = None):
        browser = mechanize.Browser()
        if cookiejar != None:
            browser.set_cookiejar(self.cookiejar)
        browser.set_handle_robots(False)
        if url != None:
            browser.open(url)
        return browser

    def submit_forms(self):
        self.forms = []
        main_url = self.deployer.get_main_url()
        for _ in xrange(MAX_RANDOM_WALK_COUNT):
            self.random_walk_for_form(self.new_browser(self.cookiejar, main_url))

    def random_walk_for_form(self, browser, depth = MAX_RANDOM_WALK_DEPTH):
        if depth == 0:
            return

        try:
            last_line_no = self.check_log()
            url = browser.geturl()
            cookiejar = browser._ua_handlers['_cookies'].cookiejar

            LOG.info('Walking URL: {}'.format(url))

            forms = list(enumerate(list(browser.forms())))
            for idx, form in forms:
                key = '{}_{}'.format(url, form.name)
                if key in self.walked_path:
                    continue
                self.walked_path.add(key)

                browser.select_form(nr = idx)
                form_stats = {
                    'url': browser.geturl(),
                    'method': form.method,
                    'inputs': []
                }
                for control in form.controls:
                    if control.type == 'text':
                        browser[control.name] = submit.gen_random_value()
                        form_stats['inputs'].append({
                            'name': control.name,
                            'type': control.type
                        })
                succ = True
                try:
                    browser.submit()
                except:
                    succ = False

                form_stats['queries'], form_stats['counter'] = self.process_logs(self.check_log(last_line_no), None)

                if all(not self.equal_form(form_stats, ret_form) for ret_form in self.forms):
                    self.forms.append(form_stats)

                if succ:
                    self.random_walk_for_form(browser, depth - 1)

                browser = self.new_browser(cookiejar, url)
        except:
            traceback.print_exc()