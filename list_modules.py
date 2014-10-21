#!/usr/bin/env python
import sys
import pkgutil
from os.path import join

sys_path = '/usr/local/lib/python2.7/dist-packages'

def iter_modules(modules, base):
    for module in modules:
        newBase = join(base, module[1])
        print newBase.replace('/', '.')
        if module[2]:
            iter_modules(pkgutil.iter_modules([join(sys_path, newBase)]), newBase)

modules = [module for module in pkgutil.iter_modules([sys_path]) if module[1] in sys.argv[1:]]
iter_modules(modules, '')

