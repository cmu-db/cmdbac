#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()
from library.models import *
from deployers import *
from drivers import *
from analyzers import *
import utils

def main():
    if len(sys.argv) not in [3, 4]:
        return
    repo_name = sys.argv[1]
    deploy_id = sys.argv[2]
    if len(sys.argv) > 3:
        database_name = sys.argv[3]
    else:
        database_name = 'MySQL'
    print 'Database : {} ...'.format(database_name)

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

    try:
        random_driver = RandomDriver(driver)
        random_driver.submit_forms()
        print random_driver.forms
        for form in random_driver.forms:
            if any(random_driver.equal_form(form, ret_form) for ret_form in driverResult['forms']):
                continue
            driverResult['forms'].append(form)
    except Exception, e:
        LOG.exception(e)

    deployer.kill_server()

    analyzer = get_analyzer(deployer)
    for form in driverResult['forms']:
        analyzer.analyze_queries(form['queries'])
    for url in driverResult['urls']:
        analyzer.analyze_queries(url['queries'])
    driverResult['statistics'] = analyzer.queries_stats
    analyzer.analyze_database()
    driverResult['statistics'].update(analyzer.database_stats)
    driverResult['informations'] = analyzer.database_informations

    deployer.save_attempt(ATTEMPT_STATUS_SUCCESS, driverResult)

if __name__ == "__main__":
    main()