import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import requests
import re
import copy
import traceback
import time
import datetime

from library.models import *
from cmudbac.settings import *
import utils
import extract
import submit
import count

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

SUBMISSION_FORMS_TIMES = 5
EDIT_DISTANCE_THRESHOLD = 3

## =====================================================================
## BASE DRIVER
## =====================================================================
class BaseDriver(object):
    
    def __init__(self, deployer):
        self.deployer = deployer
        if deployer.log_file != None:
            self.log_file = deployer.log_file
        else:
            self.log_file = LOG_FILE_LOCATION[deployer.get_database().name.lower()]
        self.forms = []
        self.urls = []

    def check_log(self, last_line_no = None):
        sql_log_file = open(self.log_file, 'r')
        if last_line_no == None:
            return len(sql_log_file.readlines())
        else:
            return sql_log_file.readlines()[last_line_no:]

    def process_query(self, query, inputs, queries):
        matched = False
        matched_query = query
        if inputs != None:
            for name, value in sorted(inputs.items(), key=lambda (x, y): len(str(y)), reverse=True):
                if str(value) in matched_query:
                    matched_query = matched_query.replace(str(value), '<span style="color:red">{}</span>'.format(name))
                    matched = True
        queries.append({'content': matched_query, 'matched': matched, 'raw': query})

    def process_logs(self, logs, inputs):
        queries = []
        current_query = None
        new_query = None
        for line in logs:
            line = line.strip()
            if self.deployer.get_database().name == 'MySQL':
                query = re.search('Query.?(.+)', line)
                # print query, line
                if query == None:
                    if len(line) > 0 and line[0].isdigit():
                        continue
                    if current_query != None:
                        current_query += ' ' + line
                        new_query = None
                else:
                    new_query = query.group(1)
            elif self.deployer.get_database().name == 'PostgreSQL':
                query = re.search('LOG:  statement: (.+)', line)
                if query == None:
                    if re.search('LOG:  duration:', line):
                        continue
                    if re.search('UTC DETAIL:', line):
                        continue
                    if re.search('LOG:  execute .*?: (.+)', line):
                        query = re.search('LOG:  execute .*?: (.+)', line)
                        new_query = query.group(1)
                    else:
                        if current_query != None:
                            current_query += ' ' + line
                            new_query = None
                else:
                    new_query = query.group(1)
            elif self.deployer.get_database().name == 'SQLite3':
                query = re.search("QUERY = u'(.+)'", line)
                if query == None:
                    if current_query != None:
                        current_query += ' ' + line
                        new_query = None
                else:
                    new_query = query.group(1)

            if new_query:
                if current_query:
                    self.process_query(current_query, inputs, queries)
                current_query = new_query
                new_query = None
        if current_query:
            self.process_query(current_query, inputs, queries)

        counter = count.count_query(queries)
        return queries, counter

    def save_screenshot(self, main_url, screenshot_path):
        try:
            from pyvirtualdisplay import Display
            display = Display(visible=0, size=(1024, 768))
            display.start()
            from selenium import webdriver
            try:
                if '127.0.0.1' in main_url or 'localhost' in main_url:
                    br = webdriver.Firefox()
                else:
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
            try:
                br.quit()
                display.stop()
            except:
                pass
            return None

    def equal_form(self, form1, form2):
        # check method first
        if form1['method'] != form2['method']:
            return False

        # check inputs
        def equal_input(input1, input2):
            for name, value in input1.iteritems():
                if name in ['value']:
                    continue
                if name not in input2:
                    return False
                if value != input2[name]:
                    return False
            return True

        inputs1 = form1['inputs']
        inputs2 = form2['inputs']
        if len(inputs1) != len(inputs2):
            return False
        for i in xrange(len(inputs1)):
            if not equal_input(inputs1[i], inputs2[i]):
                return False

        return True

    def equal_queries(self, queries1, queries2):
        n = len(queries1)
        if n != len(queries2):
            return False
        for i in xrange(n):
            if utils.edit_distance(queries1[i]['raw'], queries2[i]['raw'], EDIT_DISTANCE_THRESHOLD) > EDIT_DISTANCE_THRESHOLD:
                return False
        return True

    def equal_url(self, url1, url2):
        if url1['url'] == url2['url']:
            return True
        if self.equal_queries(url1['queries'], url2['queries']):
            return True
        return False

    def bootstrap(self):
        LOG.info('Driving : Bootstraping ...')

        # get main page
        main_url = self.deployer.get_main_url()

        # set json filename
        json_filename = 'forms{}.json'.format(self.deployer.deploy_id)

        # extract all the forms
        try:
            forms = extract.extract_all_forms(main_url, json_filename)
        except Exception, e:
            forms = []
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
            try:
                forms = extract.extract_all_forms_with_cookie(main_url, br._ua_handlers['_cookies'].cookiejar, json_filename)
            except Exception, e:
                forms = []

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
            form['queries'], form['counter'] = self.process_logs(self.check_log(last_line_no), part_inputs)
            if len(form['queries']) == 0:
                ret_forms.append(form)
                continue
                
            LOG.info('Admin: Fill in Form on {} Successfully ...'.format(form['url']))
            ret_forms.append(form)
            for i in range(SUBMISSION_FORMS_TIMES):
                try:
                    submit.fill_form_random(self.deployer.base_path, form, br)
                except:
                    pass

        return ret_forms

    def get_forms(self):
        # get main page
        main_url = self.deployer.get_main_url()

        # set json filename
        json_filename = 'forms{}.json'.format(self.deployer.deploy_id)

        # extract all the forms
        try:
            forms = extract.extract_all_forms(main_url, json_filename)
        except Exception, e:
            forms = []
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
            register_form['queries'], register_form['counter'] = self.process_logs(self.check_log(last_line_no), inputs)
        
        if register_form and len(register_form['queries']) > 0:
            register_result = USER_STATUS_SUCCESS
        else:
            register_result = USER_STATUS_FAIL
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
                login_form['queries'], login_form['counter'] = self.process_logs(self.check_log(last_line_no), inputs)
            
            if login_form and len(login_form['queries']) > 0:
                login_result = USER_STATUS_SUCCESS
            else:
                login_result = USER_STATUS_FAIL
            if login_result == USER_STATUS_FAIL:
                LOG.info('Fail to login ...')
            else:
                LOG.info('Login Successfully ...')

            if login_form != None:
                ret_forms.append(login_form)

        if br != None:
            try:
                forms = extract.extract_all_forms_with_cookie(main_url, br._ua_handlers['_cookies'].cookiejar, json_filename)
            except Exception, e:
                forms = []
                LOG.exception(e)

        # save browser
        if self.deployer.repo.project_type.id == 1 and self.browser != None: # Django
            pass
        else:
            self.browser = br

        # save forms
        for form in forms:
            if any(self.equal_form(form, ret_form) for ret_form, _ in self.forms):
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
            form['queries'], form['counter'] = self.process_logs(self.check_log(last_line_no), part_inputs)
            if len(form['queries']) == 0:
                continue

            self.forms.append((form, browser_index))
    
        return {'register': register_result, 'login': login_result, 'forms': ret_forms}

    def get_urls(self):
        # get main page
        main_url = self.deployer.get_main_url()

        # set json filename
        json_filename = 'urls{}.json'.format(self.deployer.deploy_id)

        # extract all the urls
        try:
            if self.browser != None:
                urls = extract.extract_all_urls_with_cookie(main_url, self.browser._ua_handlers['_cookies'].cookiejar, json_filename)
            else:
                urls = extract.extract_all_urls(main_url, json_filename)
        except Exception, e:
            urls = []
            LOG.exception(e)

        for url in urls:
            url['queries'] = []
            url['counter'] = {}
            last_line_no = self.check_log()
            try:
                submit.query_url(url, self.browser)
            except:
                traceback.print_exc()
                pass
            url['queries'], url['counter'] = self.process_logs(self.check_log(last_line_no), None)
            if len(url['queries']) == 0:
                continue
            if any(self.equal_url(url, ret_url) for ret_url in self.urls):
                continue

            self.urls.append(url)

    def initialize(self):
        LOG.info('Driving: Initializing ...')

        driver_results = self.get_forms()
        self.get_urls()

        return driver_results

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
                # traceback.print_exc()
                part_inputs = None
            if part_inputs == None:
                ret_forms.append(form)
                continue
            form['queries'], form['counter'] = self.process_logs(self.check_log(last_line_no), part_inputs)
            if len(form['queries']) == 0:
                continue

            LOG.info('Normal: Fill in Form on {} Successfully ...'.format(form['url']))
            ret_forms.append(form)
            for i in range(SUBMISSION_FORMS_TIMES):
                try:
                    submit.fill_form_random(self.deployer.base_path, form, self.browser)
                except:
                    pass

        return ret_forms

    def query_urls(self):
        # get main page
        main_url = self.deployer.get_main_url()

        ret_urls = []

        for url in self.urls:
            url['queries'] = []
            url['counter'] = {}

            last_line_no = self.check_log()
            try:
                submit.query_url(url, self.browser)
            except:
                # traceback.print_exc()
                pass
            url['queries'], url['counter'] = self.process_logs(self.check_log(last_line_no), None)
            if len(url['queries']) == 0:
                continue
            if any(self.equal_url(url, ret_url) for ret_url in ret_urls):
                continue

            LOG.info('Normal: Query the Url on {} Successfully ...'.format(url['url']))
            ret_urls.append(url)
        
        return ret_urls        

    def drive(self):
        LOG.info('Driving Repository: {} ...'.format(self.deployer.repo.name))

        # get main page
        main_url = self.deployer.get_main_url()

        # bootstrap
        admin_forms = self.bootstrap()
        
        # initialize
        driver_results = self.initialize()

        # submit forms
        normal_forms = self.submit_forms()

        # query urls
        urls = self.query_urls()

        # filter forms
        driver_results['forms'] += sorted(normal_forms, key=lambda x: len(x['queries']), reverse=True)
        filtered_forms = []
        for form in driver_results['forms']:
            if any(self.equal_form(form, filtered_form) for filtered_form in filtered_forms):
                continue
            filtered_forms.append(form)
        driver_results['forms'] = filtered_forms

        # save urls
        driver_results['urls'] = urls
        filtered_urls = []
        for url in driver_results['urls']:
            if any(self.equal_url(url, filtered_url) for filtered_url in filtered_urls):
                continue
            filtered_urls.append(url)
        driver_results['urls'] = filtered_urls

        LOG.info('Saving Screenshot ...')
        screenshot_path = self.save_screenshot(main_url, os.path.join(self.deployer.base_path, 'screenshot.png'))
        driver_results['screenshot'] = screenshot_path

        return driver_results
