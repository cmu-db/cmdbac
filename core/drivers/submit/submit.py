import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import mechanize
import cookielib
import string
import random
import traceback
import requests
import urlparse
from bs4 import BeautifulSoup

from patterns import patterns, match_any_pattern
import extract

def get_form_index(br, form):
    index = 0
    for f in br.forms():
        equal = True
        form['class'] = form['clazz']
        for name, value in form.iteritems():
            if name in f.attrs:
                if str(f.attrs[name]).lower() != str(value).lower():
                    equal = False
                    break
        if equal:
            break
        index = index + 1
    return index

def submit_form(form, inputs, br = None):
    if br == None:
        br = mechanize.Browser()
        cj = cookielib.LWPCookieJar() 
        br.set_cookiejar(cj)
        br.set_handle_robots(False)

    br.open(form['url'].encode("ascii","ignore"))
    br.select_form(nr=get_form_index(br, form))

    for input in form['inputs']:
        if input['name'] in inputs:
            try:
                if br.find_control(name = input['name'], type = input['type']) == None:
                    continue
                if input['type'] == 'file':
                    filename = inputs[input['name']]['filename']
                    upload_filename = os.path.basename(filename)
                    mime_type = inputs[input['name']]['mime_type']
                    br.form.add_file(open(filename), mime_type, upload_filename, name = input['name'])
                    br.form.set_all_readonly(False)
                elif input['type'] == 'checkbox':
                    br.find_control(name = input['name'], type = input['type']).selected = inputs[input['name']]
                else:
                    if br.find_control(name = input['name'], type = input['type']).readonly:
                        continue
                    if input['type'] == 'radio':
                        continue
                    br[input['name']] = inputs[input['name']]
            except:
                # traceback.print_exc()
                pass

    response = br.submit().code

    return response, br

def gen_random_value(chars = string.ascii_letters + string.digits, length = 0):
    if length == 0:
        length = random.choice(range(8, 21))
    return ''.join(random.choice(chars) for x in range(length))

def gen_random_true_false():
    return random.choice([True, False])

def gen_file(deploy_path, input):
    if input['name'] != '' and 'image' in input['name']:
        filename = os.path.join(os.path.dirname(__file__), os.pardir, "files", "image.jpg")
        mime_type = 'image/jpeg'
    else:
        filename = os.path.join(deploy_path, gen_random_value() + '.txt')
        with open(filename, 'w') as f:
            f.write(gen_random_value(length = 1000))
        f.close()
        mime_type = 'text/plain'
    return filename, mime_type

def fill_form(form, matched_patterns = {}, br = None):
    inputs = {}
    for input in form['inputs']:
        if input['value'] != '':
            continue
        for pattern_name in patterns:
            if input['type'] == 'hidden':
                continue
            pattern, value = patterns[pattern_name]
            if match_any_pattern(input['name'], pattern) or match_any_pattern(input['type'], pattern):
                if pattern_name in matched_patterns:
                    inputs[input['name']] = matched_patterns[pattern_name]
                else:
                    inputs[input['name']] = value[0]
                    matched_patterns[pattern_name] = value[0]
                break
            elif input['type'] == 'checkbox':
                inputs[input['name']] = True
            else:
                inputs[input['name']] = gen_random_value()

    response, br = submit_form(form, inputs, br)

    return matched_patterns, inputs, response, br

def fill_form_random(deploy_path, form, br):
    inputs = {}
    for input in form['inputs']:
        if input['value'] != '':
            continue
        if input['type'] == 'file':
            filename, mime_type = gen_file(deploy_path, input)
            inputs[input['name']] = {
                    'filename' : filename,
                    'mime_type': mime_type
            }
        elif input['type'] == 'checkbox':
            inputs[input['name']] = gen_random_true_false()
        else:
            inputs[input['name']] = gen_random_value()

    response, br = submit_form(form, inputs, br)

    return inputs

def submit_form_fast(form, inputs, files, session):
    new_url = urlparse.urljoin(form['url'], form['action'])
    if files == None:
        response = session.post(new_url, data = inputs)
    else:
        response = session.post(new_url, data = inputs, files = files)
    return response

def fill_form_random_fast(deploy_path, form, session):
    inputs = {}
    files = None
    response = session.get(form['url'])
    soup = BeautifulSoup(response.text)
    for input in form['inputs']:
        if input['value'] != '':
            i = soup.find('input', {"name":input['name']})
            if i:
                inputs[input['name']] = i['value']
            continue
        if input['type'] == 'file':
            if files == None:
                files = {}
            filename, mime_type = gen_file(deploy_path, input)
            upload_filename = os.path.basename(filename)
            files[input['name']] = (upload_filename, open(filename), mime_type)
        elif input['type'] == 'checkbox':
            inputs[input['name']] = gen_random_true_false()
        else:
            inputs[input['name']] = gen_random_value()

    response = submit_form_fast(form, inputs, files, session)
    
    return inputs