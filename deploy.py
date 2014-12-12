#!/usr/bin/env python
import os
import sys
import re
from utils import *

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

import django
django.setup()

from crawler.models import *

#ZIP = "prod.zip"
#DIR = "prod_dir"

def main():
    #remake_dir(DIR)
    if sys.argv[1]:
        try:
            attempt = Attempt.objects.get(id=int(sys.argv[1]))
        except:
            print 'can not find the attempt ' + sys.argv[1]
            return
    else:
        print 'please specify the attempt to deploy'
        return

    attempt_id = sys.argv[1]
    zip_file = attempt_id + '.zip'
    dir_name = attempt_id

    remake_dir(dir_name)
    try:
        download(attempt, zip_file)
    except:
        print 'can not download'
    unzip(zip_file, dir_name)

    base_dir = attempt.base_dir
    if not base_dir:
        print 'the repository do not have base_dir'
        return
    base_dir = os.path.join(dir_name, base_dir)
    print base_dir
    print base_dir
    if attempt.repo.repo_type.name == 'Django':
        vagrant_pip_clear()
        manage_file = os.path.join(base_dir, 'manage.py')
        setting_dir = attempt.setting_dir
        if not setting_dir:
            print 'the repository do not have setting file'
            return
        setting_file = os.path.join(base_dir, attempt.setting_dir, 'settings.py')
        rewrite_settings(setting_file, 'Django')
        packages = Package.objects.filter(attempt=attempt)
        out = vagrant_pip_install(packages, False)
        print out
        out = vagrant_syncdb(manage_file, "Django")
        out = kill_server("Django")
        out = vagrant_runserver(manage_file, "Django")
        urls = get_urls(os.path.dirname(setting_file), 'Django')
        print urls
        urls = list(set([re.sub(r'[\^\$]', '', url) for url in urls if '?' not in url]))
        #urls = list(set([re.sub(r'\([^)]*\)', '', url) for url in urls if '?' not in url]))
        urls = sorted(urls, key=len)
        print urls
    elif attempt.repo.repo_type.name == 'Ruby on Rails':
        rewrite_settings(base_dir, 'Ruby on Rails')
        out = install_requirements(base_dir, "Ruby on Rails")
        out = vagrant_syncdb(base_dir, "Ruby on Rails")
        out = kill_server("Ruby on Rails")
        out = vagrant_runserver(base_dir, "Ruby on Rails")
        urls = get_urls(base_dir, 'Ruby on Rails')
        print urls
        urls = [re.sub(r'\([^)]*\)', '', url) for url in urls]
        urls = list(set([url for url in urls if ':' not in url]))
        urls = sorted(urls, key=len)
        print urls
        
if __name__ == '__main__':
    main()

