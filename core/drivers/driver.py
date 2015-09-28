import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import traceback
import requests
import re

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
					query = query.replace(value, name)
					matched = True
			if matched == True:
				print query
				ret_queries.append(query)
		return ret_queries

	def drive(self, deployer):
		# get main page
		main_url = deployer.get_main_url()
		
		# extract all the forms
		forms = extract.extract_all_forms(main_url)
		ret_forms = {'others': []}

		# register
		last_line_no = self.check_log()
		register_form, info, inputs = submit.register(forms)
		if info == None:
			print 'Fail to register ...'
			return {'register': USER_STATUS_FAIL, 'login': USER_STATUS_UNKOWN}
		print 'Register Successfully ...'
		register_form['queries'] = self.match_query(self.check_log(last_line_no), inputs)
		ret_forms['register'] = register_form
			
		# login
		last_line_no = self.check_log()
		login_form, br = submit.login(forms, info)
		if login_form == None:
			print 'Fail to register ...'
			return {'register': USER_STATUS_SUCCESS, 'login': USER_STATUS_FAIL}
		print 'Login Successfully ...'
		login_form['queries'] = self.match_query(self.check_log(last_line_no), inputs)
		ret_forms['login'] = login_form
		
		forms = extract.extract_all_forms_with_cookie(main_url, br._ua_handlers['_cookies'].cookiejar)
		other_forms = filter(lambda form: form != register_form and form != login_form, forms)
		for form in other_forms:
			last_line_no = self.check_log()
			part_inputs = submit.fill_form_random(form, br)
			form['queries'] = self.match_query(self.check_log(last_line_no), part_inputs)
			ret_forms['others'].append(form)
			for i in range(5):
				submit.fill_form_random(form, br)

		print 'Fill Forms Successfully ...'

		print ret_forms
		return {'register': USER_STATUS_SUCCESS, 'login': USER_STATUS_SUCCESS, 
				'user':info, 'forms': ret_forms}
