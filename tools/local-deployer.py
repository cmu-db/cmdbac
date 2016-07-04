#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core", "utils"))

import argparse
import requests
import traceback
import json
import vagrant

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

CMDBAC_URL = "http://cmdbac.cs.cmu.edu/"

ATTEMPT_INFO_URL = "/api/attempt/{id}/info/"

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
        help='Number of threads you want to use to submit actions')
    agroup.add_argument('--timeout', type=int, metavar='T', \
        help='Timeout for submitting actions (seconds)')

    # Database Parameters
    agroup = aparser.add_argument_group('Local Database Parameters')
    agroup.add_argument('--db-type', choices=DATABASE_TYPES, \
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
    print url
    response = requests.get(url)
    return response.json()
## DEF

def run_attempt_benchmark(api_url, attempt_id, database, benchmark):
    attempt_info = get_attempt_info(api_url, attempt_id)
    print 'Running Benchmark for Attempt {}'.format(attempt_id)
    try:
        vagrant.vagrant_benchmark(attempt_info, database, benchmark)
    except Exception, e:
        traceback.print_exc() 
## DEF
    
if __name__ == "__main__":
    args = parse_args()
    
    if args["db_type"] == None:
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