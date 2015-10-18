import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import requests
import re
import copy

from crawler.models import *
from db_webcrawler.settings import *
import utils
import extract
import submit

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## MYSQL General Log Configuration
MYSQL_GENERAL_LOG_FILE = '/var/log/mysql/mysql.log'

## =====================================================================
## DRIVER
## =====================================================================
class Driver(object):
    
    def __init__(self):
        pass

    def check_log(self, last_line_no = None):
        sql_log_file = open(MYSQL_GENERAL_LOG_FILE, 'r')
        if last_line_no == None:
            return len(sql_log_file.readlines())
        else:
            return sql_log_file.readlines()[last_line_no-1:]

    def match_query(self, queries, inputs):
        ret_queries = []
        for query in queries:
            matched = False
            query = re.search('Query.?(.+)', query)
            if query == None:
                continue
            query = query.group(1)
            for name, value in sorted(inputs.items(), key=lambda (x, y): len(y), reverse=True):
                if value in query:
                    query = query.replace(value, '<span style="color:red">{}</span>'.format(name))
                    matched = True
            if matched == True:
                ret_queries.append(query)
        return ret_queries

    def save_screenshot(self, main_url, screenshot_path):
        try:
            from pyvirtualdisplay import Display
            display = Display(visible=0, size=(1024, 768))
            display.start()
            from selenium import webdriver
            try:
                from selenium.webdriver.common.proxy import *
                proxy = Proxy({
                    'proxyType': ProxyType.MANUAL,
                    'httpProxy': HTTP_PROXY
                })
                br = webdriver.Firefox(proxy=proxy)
            except:
                br = webdriver.Firefox()
            br.get(main_url)
            br.save_screenshot(screenshot_path)
            br.quit
            return screenshot_path
        except Exception, e:
            LOG.exception(e)
            return None

    def admin_drive(self, deployer):
        # get main page
        main_url = deployer.get_main_url()

        # extract all the forms
        try:
            forms = extract.extract_all_forms(main_url)
        except Exception, e:
            forms = []
            LOG.exception(e)
        ret_forms = []

        # login as admin
        br = None
        info = {
            'username': 'admin',
            'password': 'admin'
        }
        try:
            login_form, br = submit.login(forms, info)
        except Exception, e:
            login_form = br = None
            LOG.exception(e)
        # submit other forms as admin
        if br != None:
            forms = extract.extract_all_forms_with_cookie(main_url, br._ua_handlers['_cookies'].cookiejar)
        else:
            forms = []
        for form in forms:
            last_line_no = self.check_log()
            try:
                part_inputs = submit.fill_form_random(deployer.base_path, form, br)
            except:
                part_inputs = None
            if part_inputs == None:
                form['queries'] = []
                ret_forms.append(form)
                continue
            LOG.info('Admin: Fill in Form on {} Successfully ...'.format(form['url']))
            form['queries'] = self.match_query(self.check_log(last_line_no), part_inputs)
            ret_forms.append(form)
            for i in range(5):
                try:
                    submit.fill_form_random(deployer.base_path, form, br)
                except:
                    pass

        return ret_forms


    def normal_drive(self, deployer):
        # get main page
        main_url = deployer.get_main_url()

        # extract all the forms
        try:
            forms = extract.extract_all_forms(main_url)
        except Exception, e:
            forms = []
            LOG.exception(e)
        ret_forms = []

        # register as normal user
        register_result = USER_STATUS_UNKNOWN
        register_form_raw = None
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
            register_form['queries'] = self.match_query(self.check_log(last_line_no), inputs)
        if register_form != None:
            ret_forms.append(register_form)
            register_form_raw = copy.deepcopy(register_form)
            del register_form_raw['queries']

        # login as normal user
        login_result = USER_STATUS_UNKNOWN
        login_form_raw = None
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
                login_form['queries'] = self.match_query(self.check_log(last_line_no), inputs)
            if login_form != None:
                ret_forms.append(login_form)
                login_form_raw = copy.deepcopy(login_form)
                del login_form_raw['queries']

        # submit other forms as normal user(or do not login)
        if br != None:
            forms = extract.extract_all_forms_with_cookie(main_url, br._ua_handlers['_cookies'].cookiejar)
            other_forms = filter(lambda form: form not in [register_form_raw, login_form_raw], forms)
        else:
            other_forms = filter(lambda form: form not in [register_form_raw, login_form_raw], forms)
        for form in other_forms:
            last_line_no = self.check_log()
            try:
                part_inputs = submit.fill_form_random(deployer.base_path, form, br)
            except:
                part_inputs = None
            if part_inputs == None:
                form['queries'] = []
                ret_forms.append(form)
                continue
            LOG.info('Normal: Fill in Form on {} Successfully ...'.format(form['url']))
            form['queries'] = self.match_query(self.check_log(last_line_no), part_inputs)
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
        admin_forms = self.admin_drive(deployer)
        driver_results = self.normal_drive(deployer)
        driver_results['forms'] += admin_forms
        return driver_results