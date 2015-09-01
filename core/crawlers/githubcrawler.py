import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import time
import json
import re
import urllib2
import logging
import urlparse
import requests

from string import Template
from bs4 import BeautifulSoup
from datetime import datetime

from basecrawler import BaseCrawler
from crawler.models import *

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================

LOG = logging.getLogger(__name__)
LOG_handler = logging.StreamHandler()
LOG_formatter = logging.Formatter(fmt='%(asctime)s [%(filename)s:%(funcName)s:%(lineno)03d] %(levelname)-5s: %(message)s',
                                  datefmt='%m-%d-%Y %H:%M:%S')
LOG_handler.setFormatter(LOG_formatter)
LOG.addHandler(LOG_handler)
LOG.setLevel(logging.INFO)

## =====================================================================
## GITHUB CONFIGURATION
## =====================================================================

BASE_URL = "https://github.com/search?q=${query}"
GITHUB_HOST = 'https://github.com/'
API_GITHUB_REPO = 'https://api.github.com/repos/'
API_GITHUB_SLEEP = 4 # seconds

## =====================================================================
## GITHUB CRAWLER
## =====================================================================
class GitHubCrawler(BaseCrawler):
    def __init__(self, crawlerStatus, auth):
        BaseCrawler.__init__(self, crawlerStatus, auth)

        # Basic Search String
        self.template = Template(BASE_URL)
    ## DEF
    
    def next_url(self):
        # Check whether there is a next url that we need to load
        # from where we left off from our last run\
        if not self.crawlerStatus.next_url is None and not self.crawlerStatus.next_url == '':
            return self.crawlerStatus.next_url
        
        # Otherwise, compute what the next page we want to load
        args = {
            "query": self.crawlerStatus.project_type.name
        }

        return self.template.substitute(args)
    ## DEF

    def load_url(self, url):
        LOG.info("Retrieving data from %s" % url)
        request = urllib2.Request(url)
        # request.add_header('Authorization', 'token %s' % self.crawlerStatus.source.search_token)
        response = urllib2.urlopen(request)
        return response
    ## DEF

    def get_api_data(self, name):
        response = requests.get(urlparse.urljoin(API_GITHUB_REPO, name), auth=(self.auth['user'], self.auth['pass']))
        data = response.json()
        return data
    ## DEF

    def get_webpage_data(self, name):
        data = {}
        response = self.load_url(urlparse.urljoin(GITHUB_HOST, name))
        soup = BeautifulSoup(response.read())
        numbers = soup.find_all(class_='num text-emphasized')
        
        # The fields that we want to extract integers
        # The order matters here
        fields = [
            "commits_count",
            "branches_count",
            "releases_count",
            "contributors_count",
        ]
        for i in xrange(len(fields)):
            try:
                data[fields[i]] = int(re.sub("\D", "", numbers[i].string))
            except:
                data[fields[i]] = 0
        ## FOR

        return data
    ## DEF
    
    def search(self):
        # Load and parse!
        response = self.load_url(self.next_url())
        soup = BeautifulSoup(response.read())
        titles = soup.find_all(class_='title')
        LOG.info("Found %d repositories" % len(titles))
        
        # Pick through the results and find repos
        for title in titles:
            name = title.contents[1].string
            if Repository.objects.filter(name=name).exists():
                LOG.info("Repository '%s' already exists" % name)
            else:
                api_data = self.get_api_data(name)

                if api_data['stargazers_count'] < 10:
                    continue

                LOG.info("Found new repository '%s'" % name)
                webpage_data = self.get_webpage_data(name)
                
                def none2empty(string):
                    if string:
                        return string
                    else:
                        return ''

                # Create the new repository
                repo = Repository()
                repo.name = name
                repo.source = self.crawlerStatus.source
                repo.project_type = self.crawlerStatus.project_type
                repo.last_attempt = None
                repo.private = api_data['private']
                repo.description = none2empty(api_data['description'])
                repo.fork = api_data['fork']
                repo.created_at = datetime.strptime(api_data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                repo.updated_at = datetime.strptime(api_data['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
                repo.pushed_at = datetime.strptime(api_data['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
                repo.homepage = none2empty(api_data['homepage'])
                repo.size = api_data['size']
                repo.stargazers_count = api_data['stargazers_count']
                repo.watchers_count = api_data['watchers_count']
                repo.language = none2empty(api_data['language'])
                repo.has_issues = api_data['has_issues']
                repo.has_downloads = api_data['has_downloads']
                repo.has_wiki = api_data['has_wiki']
                repo.has_pages= api_data['has_pages']
                repo.forks_count = api_data['forks_count']
                repo.open_issues_count = api_data['open_issues_count']
                repo.default_branch = api_data['default_branch']
                repo.network_count = api_data['network_count']
                repo.subscribers_count = api_data['subscribers_count']
                repo.commits_count = webpage_data['commits_count']
                repo.branches_count = webpage_data['branches_count']
                repo.releases_count = webpage_data['releases_count']
                repo.contributors_count = webpage_data['contributors_count']
                repo.attempts_count = 0
                repo.save()
                LOG.info("Successfully created new repository '%s' [%d]" % (repo, repo.id))
                
                # Sleep for a little bit to prevent us from getting blocked
                time.sleep(API_GITHUB_SLEEP)
            ## IF
        ## FOR

        # Figure out what is the next page that we need to load
        next_page = soup.find(class_='next_page')
        next_url = None
        if not next_page or not next_page.has_attr('href'):
            LOG.info("No next page link found!")
            self.crawlerStatus.next_url = None
        else:
            self.crawlerStatus.next_url = GITHUB_HOST + next_page['href']
            
        # Make sure we update our crawler status
        LOG.info("Updating status for %s" % self.crawlerStatus)
        self.crawlerStatus.save()
            
        return
    ## DEF