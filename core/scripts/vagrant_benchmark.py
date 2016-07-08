#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

import argparse
import datetime
import socket
import traceback
import time
import logging
import json
from multiprocessing import Process, Queue

from deployers import *
from drivers import *
from analyzers import *
import utils

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

def run_driver(driver, timeout, queue):
    cnt = 0
    start_time = time.time()
    stop_time = start_time + timeout
    new_driver = BenchmarkDriver(driver)
    try:
        while time.time() < stop_time:
            cnt += new_driver.submit_actions()
        queue.put(cnt)
    except Exception, e:
        traceback.print_exc()
        queue.put(cnt)

def get_database_size(deployer):
    deployer.database = Database()
    deployer.database.name = 'MySQL'
    conn = deployer.get_database_connection(False)
    cur = conn.cursor()
    cur.execute('''
        SELECT Round(SUM(data_length + index_length) / 1024 / 1024, 1)
        FROM information_schema.tables 
        WHERE table_schema = 'django_app0'
    '''.format(deployer.database_config['name']))
    size = cur.fetchone()[0]
    return size

def main():
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt_info', type=str)
    parser.add_argument('--deploy_id', type=int)
    parser.add_argument('--database', type=str)
    parser.add_argument('--host', type=str)
    parser.add_argument('--port', type=int)
    parser.add_argument('--name', type=str)
    parser.add_argument('--username', type=str)
    parser.add_argument('--password', type=str)
    parser.add_argument('--num_threads', type=int)
    parser.add_argument('--timeout', type=int)
    args = parser.parse_args()

    # get args
    with open(args.attempt_info, 'r') as attempt_info_file:
        attempt_info = json.loads(attempt_info_file.read())
    deploy_id = args.deploy_id
    database_config = {
        'database': args.database,
        'host': args.host,
        'port': args.port,
        'name': args.name,
        'username': args.username,
        'password': args.password
    }
    num_threads = args.num_threads
    timeout = args.timeout

    # get deployer
    project_type = attempt_info['repo_info']['project_type']
    deployer_class = {
        1: 'DjangoDeployer',
        2: 'RoRDeployer',
        3: 'NodeDeployer',
        4: 'DrupalDeployer',
        5: 'GrailsDeployer'
    }[project_type]

    moduleName = "deployers.%s" % (deployer_class.lower())
    moduleHandle = __import__(moduleName, globals(), locals(), [deployer_class])
    klass = getattr(moduleHandle, deployer_class)

    deployer = klass(None, None, deploy_id, database_config)

    result = deployer.deploy(attempt_info)
    if result != 0:
        deployer.kill_server()
        sys.exit(-1)

    LOG.info('Running driver ...')
    driver = BaseDriver(deployer)
    
    try:
        driver.bootstrap()
        driver.initialize()
    except Exception, e:
        traceback.print_exc()
    
    actions_cnt = 0
    processes = []
    try:
        # disable logging of requests
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        # multi-processing
        queue = Queue()
        for _ in range(num_threads):
            process = Process(target = run_driver, args = (driver, timeout, queue))
            processes.append(process)
            process.start()
        for process in processes:
            process.join()
        for _ in range(num_threads):
            actions_cnt += queue.get()
    except Exception, e:
        traceback.print_exc()
    
    LOG.info('The number of actions submitted : {}'.format(actions_cnt))

    # kill server
    deployer.kill_server()

    # analyze
    LOG.info('Analyzing queries ...')
    analyzer = get_analyzer(deployer)
    for form, _ in driver.forms:
        analyzer.analyze_queries(form['queries'])
    for url in driver.urls:
        analyzer.analyze_queries(url['queries'])
    LOG.info(analyzer.queries_stats)

    # extract database info
    LOG.info('Extracting database info ...')
    analyzer.analyze_database()
    LOG.info(analyzer.database_stats)

    LOG.info('Database Size : {} '.format(get_database_size(deployer)))

    LOG.info('Finishing ...')

if __name__ == "__main__":
    main()
