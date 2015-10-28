#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
import django
django.setup()

import argparse

from crawler.models import *
from deployers import *
from drivers import *
import utils

def main():
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=str)
    parser.add_argument('--deploy_id', type=int)
    parser.add_argument('--host', type=str)
    parser.add_argument('--port', type=int)
    parser.add_argument('--name', type=str)
    parser.add_argument('--username', type=str)
    parser.add_argument('--password', type=str)
    parser.add_argument('--num_threads', type=int)
    args = parser.parse_args()

    # get args
    repo_name = args.repo
    deploy_id = args.deploy_id
    database_name = 'MySQL'
    database_config = {
        'host': args.host,
        'port': args.port,
        'name': args.name,
        'username': args.username,
        'password': args.password
    }
    num_threads = args.num_threads

    repo = Repository.objects.get(name=repo_name)
    database = Database.objects.get(name=database_name)
    
    moduleName = "deployers.%s" % (repo.project_type.deployer_class.lower())
    moduleHandle = __import__(moduleName, globals(), locals(), [repo.project_type.deployer_class])
    klass = getattr(moduleHandle, repo.project_type.deployer_class)
    deployer = klass(repo, database, deploy_id, database_config)
    if deployer.deploy() != 0:
        deployer.kill_server()
        sys.exit(-1)
    # TODO : use num_threads
    try:
        driver = Driver()
        driverResult = driver.drive(deployer)
    except Exception, e:
        LOG.exception(e)
        driverResult = {}
    deployer.kill_server()
    deployer.save_attempt(ATTEMPT_STATUS_SUCCESS, driverResult)
    # deployer.extract_database_info()

if __name__ == "__main__":
    main()