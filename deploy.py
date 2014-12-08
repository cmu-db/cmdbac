#!/usr/bin/env python
import os
from utils import *

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

import django
django.setup()

from crawler.models import *

ZIP = "prod.zip"
DIR = "prod_dir"

def main():
    if argv[1]:
        try:
            attempt = Attempt.objects.get(id=int(argv[1]))
        except:
            print 'can not find the attempt ' + argv[1]

    else:
        print 'please specify the attempt to deploy'
        return

    try:
        download(attempt, ZIP)
    except:
        print 'can not download'
    unzip(ZIP, DIR)

    base_dir = attempt.base_dir
    if base_dir = '':
        print 'the repository do not have base_dir'
        return
    if attempt.repo.repo_type.name == 'Django':
        manage_file = os.path.join(DIR, base_dir, 'manage.py')
        setting_path = attempt.setting_path
        if setting_path = '':
            print 'the repository do not have setting file'
            return
        setting_file = os.path.join(DIR, attempt.setting_path, 'settings.py')
        rewrite_settings(setting_file, 'Django')
        dependencies = Dependency.objects.filter(attempt=attempt).values_list('package', flat=True)
        vagrant_pip_install(requirement_file)

        vagrant_syncdb(manage_file, "Django")
        vagrant_runserver(manage_file, "Django")
    elif attempt.repo.repo_type.name == 'Ruby on Rails':
        base_dir = attempt.base_dir
        rewrite_settings(base_dir, 'Ruby on Rails')
        install_requirements(base_dir, "Ruby on Rails")
        vagrant_syncdb(base_dir, "Ruby on Rails")
        vagrant_runserver(manage_file, "Ruby on Rails")
        
if __name__ == '__main__':
    main()

