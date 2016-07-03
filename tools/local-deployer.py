#!/usr/bin/env python
import os, sys

import argparse
import requests
import json

ATTEMPT_INFO_URL = "http://127.0.0.1:8000/api/attempt/{id}/info/"
ATTEMPT_BENCHMARK_URL = "http://127.0.0.1:8000/api/attempt/{id}/benchmark/"

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
    url = ATTEMPT_INFO_URL.format(id = attempt_id)
    response = requests.get(url)
    return response.json()

def run_attempt_benchmark(attempt_id, database, benchmark):
    benchmark = {
        'num_threads': 1,
        'timeout': 60
    }
    payload = {
        'database': database, 
        'benchmark': benchmark
    }
    url = ATTEMPT_BENCHMARK_URL.format(id = attempt_id)
    response = requests.post(url, json = payload, stream = True, timeout = 10000)
    for chunk in response.iter_content(chunk_size=1024): 
        if chunk:
            print chunk,
    
if __name__ == "__main__":
    args = parse_args()
    
    if 'database' not in args:
        attempt_id = args.attempt
        attempt_info = get_attempt_info(attempt_id)
        print json.dumps(attempt_info, indent = 4)
    else:
        attempt_id = args.attempt
        database = {
            'database': args.database,
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
        run_attempt_benchmark(attempt_id, database, benchmark)
