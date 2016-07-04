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

def get_crawler(crawler_status, crawler_class):
    moduleName = "crawlers.%s" % (crawler_class.lower())
    moduleHandle = __import__(moduleName, globals(), locals(), [crawler_class])
    klass = getattr(moduleHandle, crawler_class)
    # FOR GITHUB
    try:
        with open(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "secrets", "secrets.json"), 'r') as auth_file:
            auth = json.load(auth_file)
    except:
        auth = None
    crawler = klass(crawler_status, auth)
    return crawler

def add_module(module_name, package_name, package_type_id, package_version):
    project_type = ProjectType.objects.get(id=package_type_id)
    Package.objects.get_or_create(name = package_name, version = package_version, project_type = project_type)
    package = Package.objects.get(name = package_name, version = package_version, project_type = project_type)
    module = Module()
    module.name = module_name
    module.package = package
    module.save()

def add_repo(repo_name, crawler_status_id, repo_setup_scripts):
    cs = CrawlerStatus.objects.get(id=crawler_status_id)
    repo_source = cs.source
    project_type = cs.project_type
    crawler = get_crawler(cs, repo_source)
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

def edit_distance(a, b, threshold = 3):
    dis = threshold + 1
    len_a = len(a)
    len_b = len(b)
    if abs(len_a - len_b) > threshold: 
        return dis
    d0 = [0] * (max(len_a, len_b) + 1)
    d1 = [0] * (max(len_a, len_b) + 1)
    for i in range(len_a + 1):
        l = max(0, i - threshold)
        r = min(len_b, i + threshold)
        minDis = threshold + 1
        for j in range(l, r + 1):
            if i == 0:
                d1[j] = j
            elif j == 0:
                d1[j] = i
            else:
                if a[i - 1] == b[j - 1]:
                    d1[j] = d0[j - 1]
                else:
                    d1[j] = d0[j - 1] + 1
                if j > l:
                    d1[j] = min(d1[j], d1[j - 1] + 1)
                if j < i + threshold:
                    d1[j] = min(d1[j], d0[j] + 1)
            minDis = min(minDis, d1[j]) 
        if minDis > threshold:
            return dis;
        d0, d1 = d1, d0

    dis = d0[len_b]
    return dis
