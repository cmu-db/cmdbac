#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbal.settings")
import django
django.setup()
from library.models import *
from deployers import *
from drivers import *
import utils

def main():
    if len(sys.argv) != 3:
        return
    repo_name = sys.argv[1]
    deploy_id = sys.argv[2]
    database_name = 'PostgreSQL'

    repo = Repository.objects.get(name=repo_name)
    database = Database.objects.get(name=database_name)
    
    moduleName = "deployers.%s" % (repo.project_type.deployer_class.lower())
    moduleHandle = __import__(moduleName, globals(), locals(), [repo.project_type.deployer_class])
    klass = getattr(moduleHandle, repo.project_type.deployer_class)
    deployer = klass(repo, database, deploy_id)
    if deployer.deploy() != 0:
        deployer.kill_server()
        sys.exit(-1)
    try:
        driver = BaseDriver(deployer)
        driverResult = driver.drive()
    except Exception, e:
        LOG.exception(e)
        driverResult = {}
    deployer.kill_server()
    deployer.save_attempt(ATTEMPT_STATUS_SUCCESS, driverResult)

if __name__ == "__main__":
    main()