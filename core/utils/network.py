import os
from string import Template
import json
import time
import requests
import logging

from run import run_command

with open(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "secrets", "secrets.json"), 'r') as auth_file:
    auth = json.load(auth_file)

def query(url):
    response = requests.get(url, auth=(auth['user'], auth['pass']), verify=False)
    return response

GITHUB_DOWNLOAD_URL_TEMPLATE = Template('https://github.com/${name}/archive/${sha}.zip')

def download_repo(attempt, zip_name):
    url = GITHUB_DOWNLOAD_URL_TEMPLATE.substitute(name=attempt.repo.name, sha=attempt.sha)
    response = query(url)
    zip_file = open(zip_name, 'wb')
    for chunk in response.iter_content(chunk_size=1024): 
        if chunk:
            zip_file.write(chunk)
            zip_file.flush()
    zip_file.close()

GITHUB_API_COMMITS_URL = Template('https://api.github.com/repos/${name}/commits')

def get_latest_sha(repo):
    url = GITHUB_API_COMMITS_URL.substitute(name=repo.name)
    response = query(url)
    data = response.json()
    time.sleep(1) 
    return data[0]['sha']

def kill_port(port):
    return run_command('fuser -n tcp -k {}'.format(port))

def block_network():
    return run_command('ufw enable')

def unblock_network():
    return run_command('ufw disable')