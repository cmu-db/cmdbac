import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import re
from urlparse import urlparse

import extract
from patterns import patterns, match_any_pattern
from submit import fill_form

def get_register_form(forms):
	register_patterns = ['register']
	for form in forms:
		if match_any_pattern(form['action'], register_patterns):
			return form
	return None

def verify_email(form, matched_patterns):
	email_file = None
	for log_file in os.listdir('/tmp/crawler'):
		if log_file.endswith('.log'):
			email_file = log_file
			break
	if not email_file:
		return matched_patterns, None

	email_content = open(os.path.join('/tmp/crawler', email_file)).read()
	verify_url = re.search('http://.+', email_content)
	if not verify_url:
		return matched_patterns, None
	verify_url = urlparse(verify_url.group(0))._replace(netloc = urlparse(form['url']).netloc)
	verify_url = verify_url.geturl()
	
	verify_forms = extract.extract_forms(verify_url)
	for verify_form in verify_forms:
		verify_form['url'] = verify_url
		matched_patterns, inputs, response, br = fill_form(verify_form, matched_patterns)

	return matched_patterns, inputs

def register(forms):
	register_form = get_register_form(forms)
	if register_form == None:
		return None
	
	matched_patterns, inputs, response, br = fill_form(register_form)
	
	if 'email' in matched_patterns:
		matched_patterns, part_inputs = verify_email(register_form, matched_patterns)
		if part_inputs != None:
			inputs.update(part_inputs)

	return register_form, matched_patterns, inputs