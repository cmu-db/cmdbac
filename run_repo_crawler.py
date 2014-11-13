#!/usr/bin/env python
import os
from utils import query
import traceback
from string import Template
from bs4 import BeautifulSoup
import time
import logging
import json
from datetime import datetime
logging.basicConfig(filename='repo_crawler.log',level=logging.DEBUG)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

import django
django.setup()

from crawler.models import *

github_host = 'https://github.com'
api_github_repo = 'https://api.github.com/repos/'


def api_get_repo(full_name):
    url = api_github_repo + full_name
    response = query(url)
    data = json.load(response)
    return data

def change_if_none(text):
    if text:
        return text
    else:
        return ""

def crawl_repo(url):
    while True:
        response = query(url)
        soup = BeautifulSoup(response.read())
        titles = soup.find_all(class_='title')
        for title in titles:
            full_name = title.contents[1].string
            if Repository.objects.filter(full_name=full_name).exists():
                logging.debug("repository already exist: " + full_name)
            else:
                logging.debug("found new repository " + full_name + ". call github api")
                data = api_get_repo(full_name)
                logging.debug(data)
                language = data['language']
                if Language.objects.filter(name=language).exists():
                    repo = Repository()
                    repo.full_name = full_name
                    repo.repo_type = Type(name="Django")
                    repo.language = Language(name=language)
                    repo.last_attempt = None
                    repo.private = data['private']
                    repo.description = change_if_none(data['description'])
                    repo.fork = data['fork']
                    repo.created_at = datetime.strptime(data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                    repo.updated_at = datetime.strptime(data['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
                    repo.pushed_at = datetime.strptime(data['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
                    repo.homepage = change_if_none(data['homepage'])
                    repo.size = data['size']
                    repo.watchers_count = data['watchers_count']
                    repo.has_issues = data['has_issues']
                    repo.has_downloads = data['has_downloads']
                    repo.has_wiki = data['has_wiki']
                    repo.has_pages= data['has_pages']
                    repo.forks_count = data['forks_count']
                    repo.open_issues_count = data['open_issues_count']
                    repo.default_branch = data['default_branch']
                    repo.network_count = data['network_count']
                    repo.subscribers_count = data['subscribers_count']
                    repo.save()
                else:
                    logging.debug('unknown language: ' + str(language))
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
            logging.debug('crawl size = ' +  str(size))
            url = template.substitute(size=size)
            logging.debug('url: ' + url)
            crawl_repo(url)
        logging.debug('crawl size > ' +  str(threshold_size))
        url = template.substitute(size='>' + str(threshold_size))
        logging.debug('url: ' + url)
        crawl_repo(url)
