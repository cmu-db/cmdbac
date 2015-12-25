import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import time
import re
import urllib
import urllib2
import logging
import urlparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import traceback

from basecrawler import BaseCrawler
from library.models import *

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
## DRUPAL CONFIGURATION
## =====================================================================

## =====================================================================
## DRUPAL CRAWLER
## =====================================================================
class DrupalCrawler(BaseCrawler):
    def __init__(self, crawlerStatus):
        BaseCrawler.__init__(self, crawlerStatus)
    ## DEF

    def load_url(self, url):
        LOG.info("Retrieving data from %s" % url)
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        return response
    ## DEF

    def get_api_data(self, name):
        data = {}
        data['url'] = self.crawlerStatus.source.get_url(name)
        response = requests.get(data['url'])
        soup = BeautifulSoup(response.text, "lxml")
        data['time'] = soup.find('time').attrs['datetime']
        return data

    def add_repository(self, name, setup_scripts):
        if Repository.objects.filter(name=name, source=self.crawlerStatus.source).exists():
            LOG.info("Repository '%s' already exists" % name)
        else:
            try:
                api_data = self.get_api_data(name)
            except:
                traceback.print_exc()
                raise Exception('Not Found')

            # Create the new repository
            repo = Repository()
            repo.name = 'drupal/' + name
            repo.source = self.crawlerStatus.source
            repo.project_type = self.crawlerStatus.project_type
            repo.last_attempt = None
            repo.created_at = datetime.fromtimestamp(int(api_data['time'])).strftime("%Y-%m-%d %H:%M:%S")
            repo.updated_at = repo.created_at
            repo.pushed_at = repo.created_at
            repo.homepage = api_data['url']
            repo.size = -1
            repo.stargazers_count = -1
            repo.watchers_count = -1
            repo.language = 'PHP'
            repo.forks_count = -1
            repo.open_issues_count = -1
            repo.default_branch = 'master'
            repo.network_count = -1
            repo.subscribers_count = -1
            repo.commits_count = -1
            repo.branches_count = -1
            repo.releases_count = -1
            repo.contributors_count = -1
            repo.setup_scripts = setup_scripts
            repo.save()
            LOG.info("Successfully created new repository '%s' [%d]" % (repo, repo.id))
        ## IF
    
    def search(self):
        pass
    ## DEF
