import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import traceback
import requests
import re
import copy

from crawler.models import *
import utils
import extract
import submit

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================


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
            from selenium import webdriver
            br = webdriver.PhantomJS()
            br.get(main_url)
            br.save_screenshot(screenshot_path)
            br.quit
            return screenshot_path
        except:
            print traceback.print_exc()
            return None


    def drive(self, deployer):
        # get main page
        main_url = deployer.get_main_url()
        
        # extract all the forms
        forms = extract.extract_all_forms(main_url)
        ret_forms = []

        # register
        register_result = USER_STATUS_UNKNOWN
        last_line_no = self.check_log()
        try:
            register_form, info, inputs = submit.register(deployer.deploy_path, forms)
        except:
            register_form = info = inputs = None
        if register_form == None or info == None or inputs == None:
            print 'Fail to register ...'
            register_result = USER_STATUS_FAIL
        else:
            print 'Register Successfully ...'
            register_result = USER_STATUS_SUCCESS
            register_form['queries'] = self.match_query(self.check_log(last_line_no), inputs)
        if register_form != None:
            ret_forms.append(register_form)
            register_form_raw = copy.deepcopy(register_form)
            del register_form_raw['queries']
        else:
            register_form_raw = None
            
        # login
        login_result = USER_STATUS_UNKNOWN
        last_line_no = self.check_log()
        try:
            login_form, br = submit.login(forms, info)
        except:
            login_form = br = None
        if login_form == None or br == None:
            print 'Fail to login ...'
            login_result = USER_STATUS_FAIL
        else:
            print 'Login Successfully ...'
            login_result = USER_STATUS_SUCCESS
            login_form['queries'] = self.match_query(self.check_log(last_line_no), inputs)
        if login_form != None:
            ret_forms.append(login_form)
            login_form_raw = copy.deepcopy(login_form)
            del login_form_raw['queries']
        else:
            login_form_raw = None
        
        # submit other forms
        if br != None:
            forms = extract.extract_all_forms_with_cookie(main_url, br._ua_handlers['_cookies'].cookiejar)
            other_forms = filter(lambda form: form not in [register_form_raw, login_form_raw], forms)
        else:
            other_forms = filter(lambda form: form not in [register_form_raw, login_form_raw], forms)
        for form in other_forms:
            last_line_no = self.check_log()
            try:
                part_inputs = submit.fill_form_random(form, br)
            except:
                part_inputs = None
            if part_inputs == None:
                print 'Fill in Form on {} Failed ...'.format(form['url'])
                continue
            form['queries'] = self.match_query(self.check_log(last_line_no), part_inputs)
            ret_forms.append(form)
            for i in range(5):
                submit.fill_form_random(form, br)

        print 'Saving Screenshot ...'
        screenshot_path = self.save_screenshot(main_url, os.path.join(deployer.deploy_path, 'screenshot.png'))



        return {'register': register_result, 'login': login_result, 
                'user':info, 'forms': ret_forms, 'screenshot': screenshot_path}
