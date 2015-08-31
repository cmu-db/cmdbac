# -*- coding: utf-8 -*-

import mechanize

def get_form_index(br, form):
	index = 0
	for f in br.forms():
		if str(f.attrs['id']) == form['id']:
			break
		index = index + 1
	return index

def submit(form):
	br = mechanize.Browser()
	br.open(form['url'])

	br.select_form(nr=get_form_index(br, form))
	for input in form['inputs']:
		br[input['name']] = 'test@test.com'
	print br.submit()