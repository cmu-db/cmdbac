import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import requests
import re
import copy
import traceback
import requests

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
    
    def __init__(self, driver, index):
        Driver.__init__(self, driver.deployer)
        self.forms = driver.forms
        self.sessions = []
        session = requests.Session()
        if driver.browser != None:
            session.cookies = driver.browser._ua_handlers['_cookies'].cookiejar
        self.sessions.append(session)
        self.sessions.append(requests.Session())
        for i in xrange(len(self.forms)):
            self.forms[i][0]['url'] = re.sub(':\d+', ':{}'.format(driver.deployer.port + index), self.forms[i][0]['url'])

    def submit_forms(self):
        forms_cnt = 0
        for form, session_index in self.forms:
            part_inputs = submit.fill_form_random_fast(self.deployer.base_path, form, self.sessions[session_index])
            forms_cnt += 1
            # LOG.info('Normal: Fill in Form on {} Successfully ...'.format(form['url']))
        return forms_cnt
