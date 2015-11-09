#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
import django
django.setup()

import argparse
import threading
import datetime
import socket
import traceback
import time

from crawler.models import *
from deployers import *
from drivers import *
from analyzers import *
import utils

forms_cnts = []

def run_driver(driver, index):
    global forms_cnts
    forms_cnts[index] = 0
    try:
        while True:
            forms_cnts[index] += driver.submit_forms()
    except Exception, e:
        pass

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
    driver = BenchmarkDriver(deployer)
    try:
        driver.bootstrap()
        driver.initialize()
    except Exception, e:
        print e
        pass

    global forms_cnts
    forms_cnts = [-1] * num_threads
    threads = []
    try:
        with utils.timeout(seconds = timeout):
            # multi-threading
            for thread_index in range(num_threads):
                thread = threading.Thread(target = run_driver, args = (driver, thread_index, ))
                thread.start()
                threads.append(thread)
    except Exception, e:
        pass

    try:
        # wait for all the threads
        for thread in threads:
            thread.join(timeout = timeout)
    except Exception, e:
        print e
    
    print 'The number of forms submitted : {}'.format(sum(forms_cnts))

    # kill server
    deployer.kill_server()

    # analyze
    print 'Analyzing queries ...'
    analyzer = Analyzer()
    for form, _ in driver.forms:
        analyzer.analyze(form['queries'])
    print analyzer.stats

    print 'Extracting database info ...'
    # extract database info
    deployer.extract_database_info()

    print 'Finishing ...'

if __name__ == "__main__":
    main()