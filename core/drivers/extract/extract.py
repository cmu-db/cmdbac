import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

import utils
import json
import traceback

def extract_form(url):
	utils.remove_file(os.path.join(os.path.dirname(__file__), 'form.json'))
	out = utils.run_command('{} && {}'.format(
		utils.cd(os.path.join(os.path.dirname(__file__))),
		'scrapy crawl form -o form.json -a start_url="{}" follow=false'.format(url)))
		
	with open(os.path.join(os.path.dirname(__file__), 'form.json')) as json_forms:
		try:
			forms = json.load(json_forms)
		except:
			print traceback.print_exc()
			forms = []

	return forms

def extract_all_forms(url):
	utils.remove_file(os.path.join(os.path.dirname(__file__), 'forms.json'))
	out = utils.run_command('{} && {}'.format(
		utils.cd(os.path.join(os.path.dirname(__file__))),
		'scrapy crawl form -o forms.json -a start_url="{}" -a follow=true'.format(url)))
	print out
		
	with open(os.path.join(os.path.dirname(__file__), 'forms.json')) as json_forms:
		try:
			forms = json.load(json_forms)
		except:
			print traceback.print_exc()
			forms = []

	return forms