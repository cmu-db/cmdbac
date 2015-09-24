import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import traceback
import requests

from crawler.models import *
import utils
import extract
import submit

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================

## =====================================================================
## DRIVER
## =====================================================================
class Driver(object):
	
	def __init__(self):
		pass

	def drive(self, deployer):
		# get main page
		main_url = deployer.get_main_url()
		
		# extract all the forms
		forms = extract.extract_all_forms(main_url)

		# register
		register_form, info = submit.register(forms)
		if info == None:
			print 'Fail to register ...'
			return {'register': USER_STATUS_FAIL, 'login': USER_STATUS_UNKOWN}
		print 'Register Successfully ...'
			
		# login
		login_form, br = submit.login(forms, info)
		if login_form == None:
			print 'Fail to register ...'
			return {'register': USER_STATUS_SUCCESS, 'login': USER_STATUS_FAIL}

		print 'Login Successfully ...'
		
		forms = extract.extract_all_forms_with_cookie(main_url, br._ua_handlers['_cookies'].cookiejar)
		forms = filter(lambda form: form != register_form and form != login_form, forms)
		for form in forms:
			for i in range(5):
				submit.fill_form_random(form, br)

		print 'Fill Forms Successfully ...'

		return {'register': USER_STATUS_SUCCESS, 'login': USER_STATUS_SUCCESS, 'forms': forms, 'queries': None}
