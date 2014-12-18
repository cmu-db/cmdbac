#!/usr/bin/env python
import os
from utils import query
from pip.index import PackageFinder, Link
from pip.download import PipSession
from pip.req import InstallRequirement
from bs4 import BeautifulSoup
import urlparse
import traceback
import re
import importlib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

import django
django.setup()

from crawler.models import *

from db_webcrawler import urls

def get_versions(package):
    host = "https://pypi.python.org/simple/"
    url = urlparse.urljoin(host, package)
    url = url + '/'
    session = PipSession()
    session.timeout = 15
    session.auth.prmpting = True
    pf = PackageFinder(find_links=[], index_urls=host, use_wheel=True, allow_external=[], allow_unverified=[], allow_all_external=False, allow_all_prereleases=False, process_dependency_links=False, session=session,)

    location = [Link(url, trusted=True)]
    req = InstallRequirement.from_line(package, None)
    versions = []
    for page in pf._get_pages(location, req):
        versions = versions + [version for _, _, version in pf._package_versions(page.links, package)]
    return versions

if __name__ == '__main__':
# e.g. add a new location
    url = "https://pypi.python.org/simple/"
    print url
    while True:
        #response = urllib2.urlopen(url)
        response = query(url)
        soup = BeautifulSoup(response.read())
        for link in soup.find_all("a"):
            package = link.get('href')
            try:
                versions = get_versions(package)
            except:
                traceback.print_exc()
                continue
            for version in versions:
                #package_type = Type.objects.get(app_type = 'Django: Library')
                pkg, created = Package.objects.get_or_create(package_type=Type(name='Django'), name=package, version=version)
                if created:
                    print "found new package: " + package + "==" + version
                else:
                    print "package already exist: " + package + "==" + version
