import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

import utils
import json
from cmudbac.settings import *

EXTRACT_WAIT_TIME = 0

def extract_forms(url, follow = "false", cookie_jar = None, filename = "forms.json"):
	utils.remove_file(os.path.join(os.path.dirname(__file__), filename))

	if cookie_jar == None:
		try:
			out = utils.run_command('{} && {}'.format(
				utils.cd(os.path.dirname(os.path.abspath(__file__))),
				'scrapy crawl form -o {} -a start_url="{}" -a follow={} -a proxy={}'.format(filename, url, follow, HTTP_PROXY)), EXTRACT_WAIT_TIME)
		except:
			out = utils.run_command('{} && {}'.format(
				utils.cd(os.path.dirname(os.path.abspath(__file__))),
				'scrapy crawl form -o {} -a start_url="{}" -a follow={}'.format(filename, url, follow)), EXTRACT_WAIT_TIME)
	else:
		cookie_jar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename.replace('.json', '.txt'))
		cookie_jar.save(cookie_jar_path)
		out = utils.run_command('{} && {}'.format(
			utils.cd(os.path.dirname(os.path.abspath(__file__))),
			'scrapy crawl form_with_cookie -o {} -a start_url="{}" -a cookie_jar={}'.format(filename, url, cookie_jar_path)), EXTRACT_WAIT_TIME)

	with open(os.path.join(os.path.dirname(__file__), filename)) as json_forms:
		forms = json.load(json_forms)

	utils.remove_file(os.path.join(os.path.dirname(__file__), filename))

	return forms

def extract_all_forms(url, filename):
	return extract_forms(url, "true", filename = filename)

def extract_all_forms_with_cookie(url, cookie_jar, filename):
	return extract_forms(url, "true", cookie_jar, filename)

def extract_urls(url, follow = "false", cookie_jar = None, filename = "urls.json"):
	utils.remove_file(os.path.join(os.path.dirname(__file__), filename))

	if cookie_jar == None:
		try:
			out = utils.run_command('{} && {}'.format(
				utils.cd(os.path.dirname(os.path.abspath(__file__))),
				'scrapy crawl url -o {} -a start_url="{}" -a follow={} -a proxy={}'.format(filename, url, follow, HTTP_PROXY)), EXTRACT_WAIT_TIME)
		except:
			out = utils.run_command('{} && {}'.format(
				utils.cd(os.path.dirname(os.path.abspath(__file__))),
				'scrapy crawl url -o {} -a start_url="{}" -a follow={}'.format(filename, url, follow)), EXTRACT_WAIT_TIME)
	else:
		cookie_jar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename.replace('.json', '.txt'))
		cookie_jar.save(cookie_jar_path)
		out = utils.run_command('{} && {}'.format(
			utils.cd(os.path.dirname(os.path.abspath(__file__))),
			'scrapy crawl url_with_cookie -o {} -a start_url="{}" -a cookie_jar={}'.format(filename, url, cookie_jar_path)), EXTRACT_WAIT_TIME)

	with open(os.path.join(os.path.dirname(__file__), filename)) as json_urls:
		urls = json.load(json_urls)

	utils.remove_file(os.path.join(os.path.dirname(__file__), filename))
	return urls

def extract_all_urls(url, filename):
	return extract_urls(url, "true", filename = filename)

def extract_all_urls_with_cookie(url, cookie_jar, filename):
	return extract_urls(url, "true", cookie_jar, filename)