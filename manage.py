#!/usr/bin/env python
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))

import utils

def vagrant_init():
    utils.vagrant_clear()
    utils.vagrant_setup()

def vagrant_final():
    utils.vagrant_clear()

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbal.settings")

    from django.core.management import execute_from_command_line

    vagrant_init()

    try:
        execute_from_command_line(sys.argv)
    finally:
        vagrant_final()



