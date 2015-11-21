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
from multiprocessing import Process, Queue

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbal.settings")
import django
django.setup()
from library.models import *
from deployers import *
from drivers import *
from analyzers import *
import utils

def run_driver(driver, timeout, queue):
    forms_cnt = 0
    start_time = time.time()
    stop_time = start_time + timeout
    new_driver = BenchmarkDriver(driver)
    try:
        while time.time() < stop_time:
            forms_cnt += new_driver.submit_forms()
        queue.put(forms_cnt)
    except Exception, e:
        traceback.print_exc()

def main():
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt', type=int)
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
    attempt_id = args.attempt
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
    attempt = Attempt.objects.get(id=attempt_id)
    repo = attempt.repo
    database = Database.objects.get(name__iexact=database_config['database'])
    runtime = attempt.runtime
    moduleName = "deployers.%s" % (repo.project_type.deployer_class.lower())
    moduleHandle = __import__(moduleName, globals(), locals(), [repo.project_type.deployer_class])
    klass = getattr(moduleHandle, repo.project_type.deployer_class)
    deployer = klass(repo, database, deploy_id, database_config, runtime)

    result = deployer.deploy(False)
    if result != 0:
        deployer.kill_server()
        sys.exit(-1)

    print 'Running driver ...'
    driver = BaseDriver(deployer)
    
    try:
        driver.bootstrap()
        driver.initialize()
    except Exception, e:
        traceback.print_exc()
    
    forms_cnt = 0
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
            forms_cnt += queue.get()
    except Exception, e:
        traceback.print_exc()
    
    print 'The number of forms submitted : {}'.format(forms_cnt)

    # kill server
    deployer.kill_server()

    # analyze
    print 'Analyzing queries ...'
    analyzer = get_analyzer(deployer)
    for form, _ in driver.forms:
        analyzer.analyze_queries(form['queries'])
    print analyzer.queries_stats

    # extract database info
    print 'Extracting database info ...'
    analyzer.analyze_database()
    print analyzer.database_stats

    print 'Finishing ...'

if __name__ == "__main__":
    main()
