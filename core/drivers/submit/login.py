import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import extract
from patterns import patterns, match_any_pattern
from submit import fill_form

def get_login_form(forms):
	login_patterns = ['login']
	for form in forms:
		if match_any_pattern(form['action'], login_patterns):
			return form
	return None

def login(forms, matched_patterns):
	login_form = get_login_form(forms)
	if login_form == None:
		return None

	matched_patterns, response = fill_form(login_form, matched_patterns)

	return response