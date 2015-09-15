# -*- coding: utf-8 -*-

import os
import mechanize

def get_form_index(br, form):
	index = 0
	for f in br.forms():
		if str(f.attrs['action']) == form['action']:
			break
		index = index + 1
	return index

def submit(form, inputs):
	br = mechanize.Browser()
	br.open(form['url'])

	br.select_form(nr=get_form_index(br, form))
	for input in form['inputs']:
		if input['name'] in inputs:
			br[input['name']] = inputs[input['name']]
	response = br.submit()
	print response

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

def register(forms):
	register_form = get_register_form(forms)
	if register_form == None:
		return None

	inputs = {}
	for input in register_form['inputs']:
		for pattern, value in patterns.values():
			if match_any_pattern(input['name'], pattern):
				inputs[input['name']] = value[0]
				break
	print inputs

	submit(register_form, inputs)

	email_file = None
	for log_file in os.listdir('/tmp/crawler'):
		if log_file.endswith('.log'):
			email_file = log_file
			break
	if not email_file:
		return None

	print open(os.path.join('/tmp/crawler', email_file)).read()