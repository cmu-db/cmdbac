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

## MYSQL General Log Configuration
MYSQL_GENERAL_LOG_FILE = '/var/log/mysql/mysql.log'

## =====================================================================
## DRIVER
## =====================================================================
class BenchmarkDriver(Driver):
    
    def __init__(self):
        pass

    def normal_drive(self, deployer):
        # get main page
        main_url = deployer.get_main_url()

        # set json filename
        json_filename = 'forms{}.json'.format(deployer.deploy_id)

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
            register_form, info, inputs = submit.register(deployer.base_path, forms)
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

        # submit other forms as normal user(or do not login)
        if br != None:
            forms = extract.extract_all_forms_with_cookie(main_url, br._ua_handlers['_cookies'].cookiejar, json_filename)
        for form in forms:
            form['queries'] = []
            form['counter'] = {}
            if any(self.equal_form(form, ret_form) for ret_form in ret_forms):
                continue
            last_line_no = self.check_log()
            try:
                part_inputs = submit.fill_form_random(deployer.base_path, form, br)
            except:
                traceback.print_exc()
                print form
                part_inputs = None
            if part_inputs == None:
                ret_forms.append(form)
                continue
            form['queries'], form['counter'] = self.process_query(self.check_log(last_line_no), part_inputs)
            if len(form['queries']) == 0:
                ret_forms.append(form)
                continue
            LOG.info('Normal: Fill in Form on {} Successfully ...'.format(form['url']))
            ret_forms.append(form)
            for i in range(5):
                try:
                    submit.fill_form_random(deployer.base_path, form, br)
                except:
                    pass

        LOG.info('Saving Screenshot ...')
        screenshot_path = self.save_screenshot(main_url, os.path.join(deployer.base_path, 'screenshot.png'))

        return {'register': register_result, 'login': login_result, 
                'user':info, 'forms': ret_forms, 'screenshot': screenshot_path}

    def drive(self, deployer):
        admin_forms = self.initialize(deployer)
        driver_results = self.normal_drive(deployer)
        driver_results['forms'] += admin_forms
        filtered_forms = []
        for form in driver_results['forms']:
            if any(self.equal_form(form, filtered_form) for filtered_form in filtered_forms):
                continue
            filtered_forms.append(form)
        driver_results['forms'] = filtered_forms
        return driver_results
