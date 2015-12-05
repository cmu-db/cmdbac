#!/usr/bin/env python
import os, sys

import argparse
import requests
import json

############ to be deleted in the future
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()
import utils
###########

ATTEMPT_URL = "http://127.0.0.1:8000/api/attempt/{id}/detail"
BENCHMARK_URL = "http://127.0.0.1:8000/api/attempt/{}/benchmark"

def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_info = subparsers.add_parser('info')
    parser_info.add_argument("-attempt", "--attempt", type=int, help='the id of the attempt')

    parser_benchmark = subparsers.add_parser('benchmark')
    parser_benchmark.add_argument('-attempt', '--attempt', type=int, help='the id of the attempt')
    parser_benchmark.add_argument('-database', '--database', type=str, help='the database you are using, e.g. mysql')
    parser_benchmark.add_argument('-host', '--host', type=str, help='the host address of your database server')
    parser_benchmark.add_argument('-port', '--port', type=int, help='the port of your database server')
    parser_benchmark.add_argument('-name', '--name', type=str, help='the name of your database')
    parser_benchmark.add_argument('-username', '--username', type=str, help='the username of your database server')
    parser_benchmark.add_argument('-password', '--password', type=str, help='the password of your database server')
    parser_benchmark.add_argument('-num_threads', '--num_threads', type=int, help='the number of threads you want to use to submit forms')
    parser_benchmark.add_argument('-timeout', '--timeout', type=int, help='the timeout for submitting forms')

    args = parser.parse_args()

    return args

def get_attempt_info(attempt_id):
    url = ATTEMPT_URL.format(id = attempt_id)
    response = requests.get(url)
    return response.json()

def run_benchmark(atempt_id, database, benchmark):
    attempt_id = 163
    if 0:
        database = {
            'database': 'mysql',
            'host': '127.0.0.1',
            'port': '3306',
            'name': 'crawler0',
            'username': 'root',
            'password': 'root'
        }
        database = {
            'database': 'postgresql',
            'host': '127.0.0.1',
            'port': '5432',
            'name': 'crawler0',
            'username': 'postgres',
            'password': 'postgres'
        }
    database = {
        'database': 'sqlite3',
        'host': '127.0.0.1',
        'port': '3306',
        'name': 'crawler0',
        'username': 'root',
        'password': 'root'
    }
    benchmark = {
        'num_threads': 1,
        'timeout': 60
    }
    data = json.dumps({
        'id': attempt_id,
        'database': database, 
        'benchmark': benchmark
    })
    response = requests.post(BENCHMARK_URL, data)
    print response.text
    ## utils.run_benchmark(attempt_id, database, benchmark)

if __name__ == "__main__":
    args = parse_args()
    # run_benchmark(1, 1, 1)
    # sys.exit(0)
    if 'database' not in args:
        attempt_id = args.attempt
        attempt_info = get_attempt_info(attempt_id)
        print attempt_info
    else:
        attempt_id = args.attempt
        database = {
            'host': args.host,
            'port': args.port,
            'name': args.name,
            'username': args.username,
            'password': args.password
        }
        benchmark = {
            'num_threads': args.num_threads,
            'timeout': args.timeout
        }
        run_benchmark(attempt_id, database, benchmark)
