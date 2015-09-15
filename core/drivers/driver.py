import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import json
import traceback

import utils
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

	def get_register_form(self, forms):
		register_patterns = ['register']
		for form in forms:
			for register_pattern in register_patterns:
				if register_pattern in form['action']:
					return form

	def register(self, forms):
		regsiter_form = self.get_register_form(forms)
		print regsiter_form

	def drive(self, deployer):
		# get main page
		main_page = deployer.get_main_page()
		
		# recursively crawl all pages and extract the forms
		utils.remove_file(os.path.join(os.path.dirname(__file__), 'extract', 'forms.json'))
		out = utils.run_command('{} && {}'.format(
			utils.cd(os.path.join(os.path.dirname(__file__), 'extract')),
			'scrapy crawl form -o forms.json -a start_url="{}"'.format(main_page)))
		
		with open(os.path.join(os.path.dirname(__file__), 'extract', 'forms.json')) as json_forms:
			try:
				forms = json.load(json_forms)
			except:
				print traceback.print_exc()
				forms = []

		print len(forms)
		self.register(forms)

		# generate input for the forms and submit them
		#for form in forms:
		#	submit.submit(form)

		out = utils.run_command('cd {} && {}'.format(
			os.path.join(os.path.dirname(__file__), 'extract'), 
			'rm -f forms.json'))
		