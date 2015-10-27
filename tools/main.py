#!/usr/bin/env python
import requests, json

ATTEMPT_URL = "http://127.0.0.1:8000/api/attempt"

def get_attempt_info():
	data = json.dumps({'id': '4'})
	response = requests.get(ATTEMPT_URL, data)
	return response.json()

def run_benchmark():
	pass


if __name__ == "__main__":
	pass	
