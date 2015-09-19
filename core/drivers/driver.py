import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import traceback

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
		info = submit.register(forms)
		if info == None:
			print 'Fail to register ...'
		else:
			print 'Register Successfully ...'
			# login
			response = submit.login(forms, info)
			if response == None:
				print 'Fail to register ...'
			else:
				print 'Login Successfully ...'