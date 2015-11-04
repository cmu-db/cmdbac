#!/usr/bin/env python
import os, sys

############ to be deleted in the future
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
import django
django.setup()
import utils
###########

import argparse
import requests
import json

ATTEMPT_URL = "http://127.0.0.1:8000/api/attempt"

def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_info = subparsers.add_parser('info')
    parser_info.add_argument("-id", "--id", type=int)

    parser_benchmark = subparsers.add_parser('benchmark')
    parser_benchmark.add_argument('-attempt', '--attempt', type=int)
    parser_benchmark.add_argument('-deploy_id', '--deploy_id', type=int)
    parser_benchmark.add_argument('-host', '--host', type=str)
    parser_benchmark.add_argument('-port', '--port', type=int)
    parser_benchmark.add_argument('-name', '--name', type=str)
    parser_benchmark.add_argument('-username', '--username', type=str)
    parser_benchmark.add_argument('-password', '--password', type=str)
    parser_benchmark.add_argument('-num_threads', '--num_threads', type=int)

    args = parser.parse_args()

    return args


def get_attempt_info():
    data = json.dumps({'id': '4'})
    response = requests.get(ATTEMPT_URL, data)
    return response.json()

def run_benchmark():
    attempt_id = 20564
    database = {
        'host': '127.0.0.1',
        'port': '3306',
        'name': 'crawler0',
        'username': 'root',
        'password': 'root'
    }
    benchmark = {
        'num_threads': 2,
        'time': 5
    }
    utils.run_benchmark(attempt_id, database, benchmark)

if __name__ == "__main__":
    # parse_args()
    run_benchmark()
