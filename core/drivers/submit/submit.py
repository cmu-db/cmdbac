# -*- coding: utf-8 -*-
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import mechanize
import re
from urlparse import urlparse

import extract

def get_form_index(br, form):
	index = 0
	for f in br.forms():
		if str(f.attrs['action']) == form['action']:
			break
		index = index + 1
	return index

def submit_form(form, inputs):
	br = mechanize.Browser()
	br.open(form['url'])

	try:
		br.select_form(nr=get_form_index(br, form))
	except:
		return
	print form
	for input in form['inputs']:
		if input['name'] in inputs:
			br[input['name']] = inputs[input['name']]
	response = br.submit().read()
	return response

def match_any_pattern(name, patterns):
	return any(pattern in name.lower() for pattern in patterns)

# Patterns
email_patterns = ['email']
email_values = ['test@gmail.com']
username_patterns = ['username', 'name']
username_values = ['test']
password_patterns = ['password']
password_values = ['Test1234--']
patterns = {
	'email': (email_patterns, email_values),
	'username': (username_patterns, username_values),
	'password': (password_patterns, password_values)
}

def get_register_form(forms):
	register_patterns = ['register']
	for form in forms:
		if match_any_pattern(form['action'], register_patterns):
			return form
	return None

def fill_form(form, matched_patterns = {}):
	inputs = {}
	for input in form['inputs']:
		for pattern_name in patterns:
			pattern, value = patterns[pattern_name]
			if match_any_pattern(input['name'], pattern):
				inputs[input['name']] = value[0]
				matched_patterns[pattern_name] = value[0]
				break

	submit_form(form, inputs)

	return matched_patterns

def verify_email(form, matched_patterns):
	email_file = None
	for log_file in os.listdir('/tmp/crawler'):
		if log_file.endswith('.log'):
			email_file = log_file
			break
	if not email_file:
		return

	email_content = open(os.path.join('/tmp/crawler', email_file)).read()
	verify_url = re.search('http://.+', email_content)
	if not verify_url:
		return
	verify_url = urlparse(verify_url.group(0))._replace(netloc = urlparse(form['url']).netloc)
	verify_url = verify_url.geturl()
	
	verify_forms = extract.extract_forms(verify_url)
	print verify_url
	for verify_form in verify_forms:
		verify_form['url'] = verify_url
		print verify_form
		matched_patterns = fill_form(verify_form, matched_patterns)

	return matched_patterns


def register(forms):
	register_form = get_register_form(forms)
	if register_form == None:
		return None

	matched_patterns = fill_form(register_form)
	
	if 'email' in matched_patterns:
		matched_patterns = verify_email(register_form, matched_patterns)

	print matched_patterns
	return matched_patterns
