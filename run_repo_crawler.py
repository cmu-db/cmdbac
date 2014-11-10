#!/usr/bin/env python
import os
from utils import query
import traceback
from string import Template
from bs4 import BeautifulSoup
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

import django
django.setup()

from crawler.models import *

github_host = 'https://github.com'

def crawl_repo(url):
    while True:
        print url
        response = query(url)
        soup = BeautifulSoup(response.read())
        titles = soup.find_all(class_='title')
        for title in titles:
            full_name = title.contents[1].string
            repo, created = Repository.objects.get_or_create(full_name=full_name, repo_type=Type(repo_type="Django"))
            if created:
                print "found new repository: " + full_name
            else:
                print "repository already exist: " + full_name
            time.sleep(1)
        next_page = soup.find(class_='next_page')
        if not next_page or not next_page.has_attr('href'):
            break;
        url = github_host + next_page['href']
if __name__ == '__main__':
    template = Template('https://github.com/search?utf8=%E2%9C%93&q=models.py+in%3Apath+filename%3Amodels.py+size%3A${size}&type=Code&ref=searchresults')
# model file less than min_size don't use database
    min_size = 60
# less then 1000 files larger than threshold_size
    threshold_size = 55000
    while True:
        for size in range(min_size, threshold_size):
            url = template.substitute(size=size)
            crawl_repo(url)
        url = template.substitute(size='>' + str(threshold_size))
        crawl_repo(url)
