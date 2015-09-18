import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import mechanize

from patterns import patterns, match_any_pattern
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

	for input in form['inputs']:
		if input['name'] in inputs:
			br[input['name']] = inputs[input['name']]
	response = br.submit().read()
	return response

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