import os
import json
import time
import requests
import logging

from run import run_command

def query(url, auth = None):
    if auth == None:
        response = requests.get(url, verify=False)
    else:
        response = requests.get(url, auth=(auth['user'], auth['pass']), verify=False)
    return response

def kill_port(port):
    return run_command('fuser -n tcp -k {}'.format(port))

def block_network():
    return run_command('ufw enable')

def unblock_network():
    return run_command('ufw disable')