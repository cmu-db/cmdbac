#!/usr/bin/env python
import os, sys

import argparse
import requests
import json

CMDBAC_URL = "http://cmdbac.cs.cmu.edu/"

ATTEMPT_INFO_URL = "/api/attempt/{id}/info/"
ATTEMPT_BENCHMARK_URL = "/api/attempt/{id}/benchmark/"

DATABASE_TYPES = (
    "mysql",
    "postgres",
    "sqlite"
)

def parse_args():
    aparser = argparse.ArgumentParser(description='CMDBAC Local Deployer Tool')
    
    # Attempt Parameters
    agroup = aparser.add_argument_group('Deployment Parameters')
    agroup.add_argument('--catalog', default=CMDBAC_URL, metavar='URL', \
        help='Catalog API URL')
    agroup.add_argument('--attempt', type=int, metavar='ID', \
        help='Id of the attempt to deploy')
    agroup.add_argument('--num_threads', type=int, default=1, metavar='N', \
        help='Number of threads you want to use to submit forms')
    agroup.add_argument('--timeout', type=int, metavar='T', \
        help='Timeout for submitting forms (seconds)')

    # Database Parameters
    agroup = aparser.add_argument_group('Local Database Parameters')
    agroup.add_argument('--db-type', choices=DATABASE_TYPES, required=True, \
        help='Database Type')
    agroup.add_argument('--db-host', type=str, \
        help='Database Hostname')
    agroup.add_argument('--db-port', type=int, \
        help='Databsae Port')
    agroup.add_argument('--db-name', type=str, \
        help='Database Name')
    agroup.add_argument('--db-user', type=str, \
        help='Database User')
    agroup.add_argument('--db-pass', type=str, \
        help='Database Password')

    return vars(aparser.parse_args())
## DEF

def get_attempt_info(api_url, attempt_id):
    url = api_url + ATTEMPT_INFO_URL.format(id = attempt_id)
    response = requests.get(url)
    return response.json()
## DEF

def run_attempt_benchmark(api_url, attempt_id, database, benchmark):
    benchmark = {
        'num_threads': 1,
        'timeout': 60
    }
    payload = {
        'database': database, 
        'benchmark': benchmark
    }
    url = api_url + ATTEMPT_BENCHMARK_URL.format(id = attempt_id)
    response = requests.post(url, json = payload, stream = True, timeout = 10000)
    for chunk in response.iter_content(chunk_size=1024): 
        if chunk:
            print chunk,
## DEF
    
if __name__ == "__main__":
    args = parse_args()
    
    if 'db_type' not in args:
        attempt_info = get_attempt_info(args["catalog"], args["attempt"])
        print json.dumps(attempt_info, indent = 4)
    else:
        database = {
            'database': args["db_type"],
            'host':     args["db_host"],
            'port':     args["db_port"],
            'name':     args["db_name"],
            'username': args["db_user"],
            'password': args["db_pass"]
        }
        benchmark = {
            'num_threads': args["num_threads"],
            'timeout': args["timeout"]
        }
        run_attempt_benchmark(args["catalog"], args["attempt"], database, benchmark)
## MAIN