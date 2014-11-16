#!/usr/bin/env python
import os
from os.path import join
from utils import run_command
import time
import pkgutil
import traceback
import socket
import logging

package_deployer_logger = logging.getLogger('package_deployer')
package_deployer_logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('package_deployer.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
package_deployer_logger.addHandler(fh)
package_deployer_logger.addHandler(ch)

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
    modules = list(pkgutil.iter_modules([join(sys_path, path)]))
    logging.getLogger('package_deployer').debug('found modules: ')
    logging.getLogger('package_deployer').debug(modules)
    return modules

def iter_modules_recur(package, modules, base):
    for module in modules:
        newBase = join(base, module[1])
        module_name = newBase.replace('/', '.')
        logging.getLogger('package_deployer').debug('found module: ' + module_name)
        obj, created = Module.objects.get_or_create(name=module_name, package=package)
        if created:
            logging.getLogger('package_deployer').debug('found new module: ' + obj.name)
        else:
            logging.getLogger('package_deployer').debug('module already exists: ' + obj.name)

        if module[2]:
            iter_modules_recur(package, pkgutil.iter_modules([join(sys_path, newBase)]), newBase)

if __name__ == '__main__':
    pip_clear()
    num_hosts = 3
    while True:
        host_id = int(socket.gethostname()[3]) - 1
        packages = Package.objects.exclude(pk__in=Module.objects.values_list('package', flat=True))
        packages = [package for package in packages if package.id % num_hosts == host_id]
        for package in packages:
            logging.getLogger('package_deployer').debug('try to install: ' + package.name + '==' + package.version + 'locally')
            try:
                pip_install(package)
                modules = iter_modules('')
                if len(modules):
                    iter_modules_recur(package, modules, '')
                else:
                    module, created = Module.objects.get_or_create(name='package_install_failed', package=package)
                    if created:
                        logging.getLogger('package_deployer').debug('found new module: ' + module.name)
                    else:
                        logging.getLogger('package_deployer').debug('module already exists: ' + module.name)
            except:
                logging.getLogger('package_deployer').debug(traceback.print_exc())
            pip_clear()
        time.sleep(1)
