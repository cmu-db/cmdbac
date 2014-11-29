#!/usr/bin/env python

import os
from utils import query
import traceback
from bs4 import BeautifulSoup
import time
import logging
import json
from datetime import datetime
from meta import metas
import re
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

def crawl_webpage(repo):
    url = github_host + '/' + repo.full_name
    response = query(url)
    soup = BeautifulSoup(response.read())
    numbers = soup.find_all(class_='num text-emphasized')
    print repo.full_name
    print numbers
    try:
        repo.commits_count = int(re.sub("\D", "", numbers[0].string))
    except:
        repo.commits_count = 0
    try:
        repo.branches_count = int(re.sub("\D", "", numbers[1].string))
    except:
        repo.branches_count = 0
    try:
        repo.releases_count = int(re.sub("\D", "", numbers[2].string))
    except:
        repo.releases_count = 0
    try:
        repo.contributors_count = int(re.sub("\D", "", numbers[3].string))
    except:
        repo.contributors_count = 0

def crawl_repo(url, meta):
    while True:
        response = query(url)
        soup = BeautifulSoup(response.read())
        titles = soup.find_all(class_='title')
        for title in titles:
            full_name = title.contents[1].string
            if Repository.objects.filter(full_name=full_name).exists():
                print("repository already exist: " + full_name)
            else:
                print("found new repository " + full_name + ". call github api")
                data = api_get_repo(full_name)
                print(data)
                language = data['language']
                if Language.objects.filter(name=language).exists():
                    repo = Repository()
                    repo.full_name = full_name
                    repo.repo_type = Type(name=meta.name)
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
                    repo.stargazers_count = data['stargazers_count']
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
                    crawl_webpage(repo)
                    repo.save()
                else:
                    print('unknown language: ' + str(language))
            time.sleep(1)
        next_page = soup.find(class_='next_page')
        if not next_page or not next_page.has_attr('href'):
            break;
        url = github_host + next_page['href']


if __name__ == '__main__':
    while True:
        for meta in metas:
            print('crawler meta: ')
            print(meta.__dict__)
            if meta.cur_size == meta.threshold_size:
                url = meta.template.substitue(size='>'+str(meta.cur_size))
                crawl_repo(url, meta)
                meta.cur_size = meta.min_size
            else:
                url = meta.template.substitute(size=meta.cur_size)
                crawl_repo(url, meta)
                meta.cur_size = meta.cur_size + 1
