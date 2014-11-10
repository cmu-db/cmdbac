#!/usr/bin/env python
import os
from os.path import join
from utils import run_command
import time
import pkgutil
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

import django
django.setup()

from crawler.models import *

def pip_clear():
    command = "rm -rf /tmp/pip/"
    run_command(command)

def pip_install(package):
    command = "pip install --user --no-deps --build /tmp/pip/build " + package.name + '==' + package.version
    run_command(command)

sys_path = '/tmp/pip/lib/python2.7/site-packages'
def iter_modules(path):
    return list(pkgutil.iter_modules([join(sys_path, path)]))

def iter_modules_recur(package, modules, base):
    for module in modules:
        newBase = join(base, module[1])
        module_name = newBase.replace('/', '.')
        print """+++++++++++++++++++++++++++++
        found module: """ + module_name
        obj, created = Module.objects.get_or_create(name=module_name, package=package)
        if created:
            print 'found new module: ' + obj.name
        else:
            print 'module already exist: ' + obj.name

        if module[2]:
            iter_modules_recur(package, pkgutil.iter_modules([join(sys_path, newBase)]), newBase)

if __name__ == '__main__':
    pip_clear()
    while True:
        packages = Package.objects.exclude(pk__in=Module.objects.values_list('package', flat=True))
        for package in packages:
            print 'try to install: ' + package.name + '==' + package.version + 'locally'
            try:
                pip_install(package)
                modules = iter_modules('')
                if len(modules):
                    iter_modules_recur(package, modules, '')
                else:
                    module, created = Module.objects.get_or_create(name='package_install_failed', package=package)
                    if created:
                        print 'found new module: ' + module.name
            except:
                traceback.print_exc()
            pip_clear()
        time.sleep(1)

