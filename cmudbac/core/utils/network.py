# stdlib imports
import json
import logging
import os
import time
# third-party imports
import requests
# local imports
from .run import run_command


def block_network():
    return run_command('ufw enable')

def kill_port(port):
    return run_command('fuser -n tcp -k {}'.format(port))

def query(url, auth=None, verify=True):
    if auth == None:
        response = requests.get(url, verify=verify)
    else:
        response = requests.get(url, auth=(auth['user'], auth['pass']), verify=verify)

    return response

def unblock_network():
    return run_command('ufw disable')
