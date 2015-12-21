#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

import json
import logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()
import library
from library.models import *
import utils

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

def add_module(module_name, package_name, package_type_id, package_version):
    project_type = ProjectType.objects.get(id=package_type_id):
    package = Package.objects.get_or_create(name = package_name, version = package_version)
    module = Module()
    module.name = module_name
    module.package = package
    module.save()

def add_repo(repo_name, crawler_status_id, repo_setup_scripts):
    for cs in CrawlerStatus.objects.filter(id=crawler_status_id):
        repo_source = cs.source
        project_type = cs.project_type

        moduleName = "crawlers.%s" % (repo_source.crawler_class.lower())
        moduleHandle = __import__(moduleName, globals(), locals(), [repo_source.crawler_class])
        klass = getattr(moduleHandle, repo_source.crawler_class)
        with open(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "secrets", "secrets.json"), 'r') as auth_file:
            auth = json.load(auth_file)
        crawler = klass(cs, auth)

        crawler.add_repository(repo_name, repo_setup_scripts)

def deploy_repo(repo_name, database = 'PostgreSQL'):
    repo = Repository.objects.get(name=repo_name)
    print 'Attempting to deploy {} using {} ...'.format(repo, repo.project_type.deployer_class)
    try:
        result = utils.vagrant_deploy(repo, 0, database)
    except Exception, e:
        LOG.exception(e)
        raise e
    return result

def delete_repo(repo_name):
    for repo in Repository.objects.filter(name=repo_name):
        repo.delete()