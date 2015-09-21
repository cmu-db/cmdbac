import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import mechanize
import cookielib
import traceback

from patterns import patterns, match_any_pattern
import extract

def get_form_index(br, form):
	index = 0
	for f in br.forms():
		if str(f.attrs.get('action', '')) == form['action']:
			break
		if str(f.attrs.get('actions', '')) == form['action']:
				break
		index = index + 1
	return index

def submit_form(form, inputs):
	br = mechanize.Browser()
	cj = cookielib.LWPCookieJar() 
	br.set_cookiejar(cj)

	try:
		br.open(form['url'])
		br.select_form(nr=get_form_index(br, form))
	except:
		print traceback.print_exc()
		return

	for input in form['inputs']:
		if input['name'] in inputs:
			br[input['name']] = inputs[input['name']]
	response = br.submit().read()
	return response, br

def fill_form(form, matched_patterns = {}):
	inputs = {}
	for input in form['inputs']:
		for pattern_name in patterns:
			pattern, value = patterns[pattern_name]
			if match_any_pattern(input['name'], pattern):
				if pattern_name in matched_patterns:
					inputs[input['name']] = matched_patterns[pattern_name]
				else:
					inputs[input['name']] = value[0]
					matched_patterns[pattern_name] = value[0]
				break

	try:
		response, br = submit_form(form, inputs)
	except:
		print traceback.print_exc()
		return None, None, None

	return matched_patterns, response, br