#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *

def main():
    for repo in Repository.objects.exclude(successful_project = True):
        if Attempt.objects.filter(repo = repo).filter(result = 'OK'):
            repo.successful_project = True
            repo.save()


if __name__ == '__main__':
    main()