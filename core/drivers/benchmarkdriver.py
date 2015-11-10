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

    def initialize(self):
        # get main page
        main_url = self.deployer.get_main_url()

        # set json filename
        json_filename = 'forms{}.json'.format(self.deployer.deploy_id)

        # extract all the forms
        try:
            forms = extract.extract_all_forms(main_url, json_filename)
        except Exception, e:
            forms = []
            LOG.exception(e)
        ret_forms = []

        # register as normal user
        register_result = USER_STATUS_UNKNOWN
        last_line_no = self.check_log()
        try:
            register_form, info, inputs = submit.register(self.deployer.base_path, forms)
        except Exception, e:
            register_form = info = inputs = None
            LOG.exception(e)
        if register_form == None or info == None or inputs == None:
            LOG.info('Fail to register ...')
            register_result = USER_STATUS_FAIL
        else:
            LOG.info('Register Successfully ...')
            register_result = USER_STATUS_SUCCESS
            register_form['queries'], register_form['counter'] = self.process_query(self.check_log(last_line_no), inputs)
        if register_form != None:
            ret_forms.append(register_form)

        # login as normal user
        login_result = USER_STATUS_UNKNOWN
        br = None
        if register_result == USER_STATUS_SUCCESS:
            last_line_no = self.check_log()
            try:
                login_form, br = submit.login(forms, info)
            except Exception, e:
                login_form = br = None
                LOG.exception(e)
            if login_form == None or br == None:
                LOG.info('Fail to login ...')
                login_result = USER_STATUS_FAIL
            else:
                LOG.info('Login Successfully ...')
                login_result = USER_STATUS_SUCCESS
                login_form['queries'], login_form['counter'] = self.process_query(self.check_log(last_line_no), inputs)
            if login_form != None:
                ret_forms.append(login_form)

        if br != None:
            forms = extract.extract_all_forms_with_cookie(main_url, br._ua_handlers['_cookies'].cookiejar, json_filename)

        # save browser
        self.browser = br

        # save forms
        for form in forms:
            last_line_no = self.check_log()
            browser = None
            try:
                part_inputs = submit.fill_form_random(self.deployer.base_path, form, self.browser)
            except:
                part_inputs = None
            if part_inputs == None:
                browser = None
                try:
                    part_inputs = submit.fill_form_random(self.deployer.base_path, form, None)
                except:
                    part_inputs = None
            else:
                try:
                    _, browser = submit.login(forms, info)
                except:
                    part_inputs = None
            if part_inputs == None:
                continue
            form['queries'], form['counter'] = self.process_query(self.check_log(last_line_no), part_inputs)
            if len(form['queries']) == 0:
                continue
            self.forms.append((form, browser))
    
        return {'register': register_result, 'login': login_result, 'forms': ret_forms}

    def submit_forms(self):
        forms_cnt = 0
        for form, browser in self.forms:
            part_inputs = submit.fill_form_random(self.deployer.base_path, form, browser)
            forms_cnt += 1
            # LOG.info('Normal: Fill in Form on {} Successfully ...'.format(form['url']))
        return forms_cnt
