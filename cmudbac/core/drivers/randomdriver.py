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
from . import extract
from . import submit
from . import count
from .basedriver import BaseDriver

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

MAX_RANDOM_WALK_DEPTH = 5

## =====================================================================
## RANDOM DRIVER
## =====================================================================
class RandomDriver(BaseDriver):

    def __init__(self, driver):
        self.driver = driver
        self.start_urls = set([url['url'] for url in driver.urls])
        self.database = self.driver.database
        if driver.browser != None:
            self.cookiejar = driver.browser._ua_handlers['_cookies'].cookiejar
        self.walked_path = set()
        self.log_file = driver.log_file

    def new_browser(self, cookiejar = None, url = None):
        browser = mechanize.Browser()
        if cookiejar != None:
            browser.set_cookiejar(self.cookiejar)
        browser.set_handle_robots(False)
        if url != None:
            browser.open(url)
        return browser

    def start(self):
        self.forms = []
        self.urls = []
        for url in self.start_urls:
            self.random_walk(self.new_browser(self.cookiejar, url))

    def random_walk(self, browser, depth = MAX_RANDOM_WALK_DEPTH):
        if depth == 0:
            return

        try:
            last_line_no = self.check_log()
            browser_url = browser.geturl()
            cookiejar = browser._ua_handlers['_cookies'].cookiejar

            LOG.info('Walking URL: {}'.format(browser_url))

            forms = list(enumerate(list(browser.forms())))
            for idx, form in forms:
                key = '{}_{}'.format(browser_url, form.name)
                if key in self.walked_path:
                    continue
                self.walked_path.add(key)

                browser.select_form(nr = idx)
                form_stats = {
                    'url': browser_url,
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
                    traceback.print_exc()
                    browser.submit()
                except:
                    succ = False

                form_stats['queries'], form_stats['counter'] = self.process_logs(self.check_log(last_line_no), None)

                if all(not self.equal_form(form_stats, ret_form) for ret_form in self.forms):
                    self.forms.append(form_stats)

                if succ:
                    self.random_walk(browser, depth - 1)

                browser = self.new_browser(cookiejar, browser_url)

            links = list(browser.links())
            for link in links:
                key = link.url
                if key in self.walked_path:
                    continue
                self.walked_path.add(key)

                url = {
                    'url': link.url,
                    'queries': [],
                    'counter': {}
                }

                succ = True
                try:
                    browser.follow_link(link)
                except:
                    traceback.print_exc()
                    succ = False

                url['queries'], url['counter'] = self.process_logs(self.check_log(last_line_no), None)

                if any(self.equal_url(url, ret_url) for ret_url in self.urls):
                    continue

                if succ:
                    self.random_walk(browser, depth - 1)

                browser = self.new_browser(cookiejar, browser_url)

        except:
            traceback.print_exc()