import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

import utils
import json
import traceback

def extract_forms(url, follow = "false", cookie_jar = None):
	utils.remove_file(os.path.join(os.path.dirname(__file__), 'forms.json'))
	if cookie_jar == None:
		out = utils.run_command('{} && {}'.format(
			utils.cd(os.path.dirname(os.path.abspath(__file__))),
			'scrapy crawl form -o forms.json -a start_url="{}" -a follow={}'.format(url, follow)))
	else:
		cookie_jar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookie_jar.txt")
		cookie_jar.save(cookie_jar_path)
		out = utils.run_command('{} && {}'.format(
			utils.cd(os.path.dirname(os.path.abspath(__file__))),
			'scrapy crawl form_with_cookie -o forms.json -a start_url="{}" -a cookie_jar={}'.format(url, cookie_jar_path)))
		
	with open(os.path.join(os.path.dirname(__file__), 'forms.json')) as json_forms:
		forms = json.load(json_forms)
		
	return forms

def extract_all_forms(url):
	return extract_forms(url, "true")

def extract_all_forms_with_cookie(url, cookie_jar):
	return extract_forms(url, "true", cookie_jar)