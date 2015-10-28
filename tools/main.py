#!/usr/bin/env python
import os, sys

# to be deleted in the future
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
import django
django.setup()
import utils
#

import requests
import json

ATTEMPT_URL = "http://127.0.0.1:8000/api/attempt"

def get_attempt_info():
	data = json.dumps({'id': '4'})
	response = requests.get(ATTEMPT_URL, data)
	return response.json()

def run_benchmark():
	database = {
		'host': '127.0.0.1',
		'port': '3306',
		'name': 'crawler0',
		'username': 'root',
		'password': 'root'
	}
	benchmark = {
		'num_threads': 1
	}
	utils.run_benchmark(4, database, benchmark)


if __name__ == "__main__":
	run_benchmark()
