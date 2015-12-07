#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *
import utils

def main():
    num_
    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        if len(

if __name__ == '__main__':
    main()
