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

from crawler.models import *
from deployers import *
from drivers import *
import utils

def run_driver(driver):
    try:
        driver.submit_forms()
    except Exception, e:
        LOG.exception(e)

def main():
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt', type=int)
    parser.add_argument('--deploy_id', type=int)
    parser.add_argument('--host', type=str)
    parser.add_argument('--port', type=int)
    parser.add_argument('--name', type=str)
    parser.add_argument('--username', type=str)
    parser.add_argument('--password', type=str)
    parser.add_argument('--num_threads', type=int)
    parser.add_argument('--time', type=int)
    args = parser.parse_args()

    # get args
    attempt_id = args.attempt
    deploy_id = args.deploy_id
    database_config = {
        'host': args.host,
        'port': args.port,
        'name': args.name,
        'username': args.username,
        'password': args.password
    }
    num_threads = args.num_threads
    time = args.time

    # get deployer
    attempt = Attempt.objects.get(id=attempt_id)
    repo = attempt.repo
    database = attempt.database
    moduleName = "deployers.%s" % (repo.project_type.deployer_class.lower())
    moduleHandle = __import__(moduleName, globals(), locals(), [repo.project_type.deployer_class])
    klass = getattr(moduleHandle, repo.project_type.deployer_class)
    deployer = klass(repo, database, deploy_id, database_config)

    result = deployer.deploy(False)
    if result != 0:
        deployer.kill_server()
        benchmark.delete()
        sys.exit(-1)

    try:
        with utils.timeout(seconds = time):
            driver = BenchmarkDriver(deployer)
            driver.bootstrap()
            driver.initialize()

            # multi-threading
            threads = []
            for _ in range(num_threads - 1):
                thread = threading.Thread(target = run_driver, args = (driver, ))
                thread.start()
                threads.append(thread)

            # wait for all the threads
            driver.submit_forms()
            for thread in threads:
                thread.join()
    except:
        pass
    
    # finish up
    deployer.kill_server()
    # deployer.save_attempt(ATTEMPT_STATUS_SUCCESS)
    # deployer.extract_database_info()

if __name__ == "__main__":
    main()