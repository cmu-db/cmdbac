import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import requests
import re
import copy
import traceback

from library.models import *
from cmudbal.settings import *
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
class Driver(object):
    
    def __init__(self, deployer):
        self.deployer = deployer
        self.forms = []

    def check_log(self, last_line_no = None):
        sql_log_file = open(MYSQL_GENERAL_LOG_FILE, 'r')
        if last_line_no == None:
            return len(sql_log_file.readlines())
        else:
            return sql_log_file.readlines()[last_line_no-1:]

    def process_query(self, queries, inputs):
        ret_queries = []
        for query in queries:
            matched = False
            query = re.search('Query.?(.+)', query)
            if query == None:
                continue
            query = query.group(1)
            for name, value in sorted(inputs.items(), key=lambda (x, y): len(str(y)), reverse=True):
                if str(value) in query:
                    query = query.replace(value, '<span style="color:red">{}</span>'.format(name))
                    matched = True
            ret_queries.append({'content': query, 'matched': matched})
        counter = count.count_query(queries)
        return ret_queries, counter

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
            except Exception, e:
                LOG.exception(e)
                br = webdriver.Firefox()
            br.get(main_url)
            br.save_screenshot(screenshot_path)
            br.quit()
            display.stop()
            return screenshot_path
        except Exception, e:
            LOG.exception(e)
            br.quit()
            display.stop()
            return None

    def equal_form(self, form1, form2):
        for name, value in form1.iteritems():
            if name in ['class', 'queries', 'url', 'counter', 'admin']:
                continue
            if name not in form2:
                return False
            if value != form2[name]:
                return False
        return True

    def bootstrap(self):
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
            forms = extract.extract_all_forms_with_cookie(main_url, br._ua_handlers['_cookies'].cookiejar, json_filename)
    
        # save browser
        self.browser = br

        for form in forms:
            if any(self.equal_form(form, ret_form) for ret_form in ret_forms):
                continue
            last_line_no = self.check_log()
            try:
                part_inputs = submit.fill_form_random(self.deployer.base_path, form, br)
            except:
                part_inputs = None
            form['admin'] = True
            if part_inputs == None:
                ret_forms.append(form)
                continue
            form['queries'], form['counter'] = self.process_query(self.check_log(last_line_no), part_inputs)
            if len(form['queries']) == 0:
                ret_forms.append(form)
                continue
            LOG.info('Admin: Fill in Form on {} Successfully ...'.format(form['url']))
            ret_forms.append(form)
            for i in range(5):
                try:
                    submit.fill_form_random(self.deployer.base_path, form, br)
                except:
                    pass

        return ret_forms

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
            register_result = USER_STATUS_FAIL
        else:
            register_form['queries'], register_form['counter'] = self.process_query(self.check_log(last_line_no), inputs)
        if len(register_form['queries']) == 0:
            register_result = USER_STATUS_FAIL
        else:
            register_result = USER_STATUS_SUCCESS
        if register_result == USER_STATUS_FAIL:
            LOG.info('Fail to register ...')
        else:
            LOG.info('Register Successfully ...')
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
                login_result = USER_STATUS_FAIL
            else:
                login_form['queries'], login_form['counter'] = self.process_query(self.check_log(last_line_no), inputs)
            if len(login_form['queries']) == 0:
                login_result = USER_STATUS_FAIL
            else:
                login_result = USER_STATUS_SUCCESS
            if login_result == USER_STATUS_FAIL:
                LOG.info('Fail to login ...')
            else:
                LOG.info('Login Successfully ...')
            if login_form != None:
                ret_forms.append(login_form)

        if br != None:
            forms = extract.extract_all_forms_with_cookie(main_url, br._ua_handlers['_cookies'].cookiejar, json_filename)

        # save browser
        if self.deployer.repo.project_type.id == 1 and self.browser != None: # Django
            pass
        else:
            self.browser = br

        # save forms
        for form in forms:
            if any(self.equal_form(form, ret_form) for ret_form in self.forms):
                continue
            last_line_no = self.check_log()
            browser_index = 0
            try:
                part_inputs = submit.fill_form_random(self.deployer.base_path, form, br)
            except:
                part_inputs = None
            if part_inputs == None:
                browser_index = 1
                try:
                    part_inputs = submit.fill_form_random(self.deployer.base_path, form, None)
                except:
                    part_inputs = None
            if part_inputs == None:
                continue
            form['queries'], form['counter'] = self.process_query(self.check_log(last_line_no), part_inputs)
            if len(form['queries']) == 0:
                continue
            self.forms.append((form, browser_index))
    
        return {'register': register_result, 'login': login_result, 'forms': ret_forms}

    def submit_forms(self):
        # get main page
        main_url = self.deployer.get_main_url()

        ret_forms = []

        for form, browser_index in self.forms:
            form['queries'] = []
            form['counter'] = {}
            if any(self.equal_form(form, ret_form) for ret_form in ret_forms):
                continue
            last_line_no = self.check_log()
            try:
                if browser_index == 0:
                    part_inputs = submit.fill_form_random(self.deployer.base_path, form, self.browser)
                else:
                    part_inputs = submit.fill_form_random(self.deployer.base_path, form, None)
            except:
                traceback.print_exc()
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
                    submit.fill_form_random(self.deployer.base_path, form, self.browser)
                except:
                    pass

        return ret_forms

    def drive(self):
        # get main page
        main_url = self.deployer.get_main_url()

        admin_forms = self.bootstrap()
        
        driver_results = self.initialize()

        normal_forms = self.submit_forms()

        # filter forms
        driver_results['forms'] += sorted(normal_forms, key=lambda x: len(x['queries']), reverse=True)
        filtered_forms = []
        for form in driver_results['forms']:
            if any(self.equal_form(form, filtered_form) for filtered_form in filtered_forms):
                continue
            filtered_forms.append(form)
        driver_results['forms'] = filtered_forms

        LOG.info('Saving Screenshot ...')
        screenshot_path = self.save_screenshot(main_url, os.path.join(self.deployer.base_path, 'screenshot.png'))
        driver_results['screenshot'] = screenshot_path

        return driver_results
