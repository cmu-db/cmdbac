import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import time
import re
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import logging
import urllib.parse
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import traceback

from .basecrawler import BaseCrawler
from library.models import *
import utils

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
BASE_URL = 'https://www.drupal.org/project/{name}'
COMMIT_URL = 'https://www.drupal.org/node/{sha}'
SEARCH_URL = 'https://www.drupal.org/project/project_distribution'
DRUPAL_HOST = 'https://www.drupal.org'
DRUPAL_SLEEP = 1

## =====================================================================
## DRUPAL CRAWLER
## =====================================================================
class DrupalCrawler(BaseCrawler):
    def __init__(self, crawlerStatus, auth):
        BaseCrawler.__init__(self, crawlerStatus)
    ## DEF

    def next_url(self):
        # Check whether there is a next url that we need to load
        # from where we left off from our last run\
        if not self.crawlerStatus.next_url is None and not self.crawlerStatus.next_url == '':
            return self.crawlerStatus.next_url

        # Otherwise, compute what the next page we want to load
        return SEARCH_URL
    ## DEF

    def search(self):
        # Load and parse!
        response = utils.query(self.next_url())
        soup = BeautifulSoup(response.text)
        titles = soup.find_all(class_='node-project-distribution')
        LOG.info("Found %d repositories" % len(titles))

        # Pick through the results and find repos
        for title in titles:
            name = title.contents[1].contents[0]['href'].split('/')[2]
            try:
                self.add_repository(name)
            except:
                traceback.print_exc()
            # Sleep for a little bit to prevent us from getting blocked
            time.sleep(DRUPAL_SLEEP)
        ## FOR

        # Figure out what is the next page that we need to load
        try:
            next_page = soup.find(class_='pager-next').contents[0]
        except:
            next_page = None
        if not next_page or not next_page.has_attr('href'):
            LOG.info("No next page link found!")
            self.crawlerStatus.next_url = None
        else:
            self.crawlerStatus.next_url = DRUPAL_HOST + next_page['href']

        # Make sure we update our crawler status
        LOG.info("Updating status for %s" % self.crawlerStatus)
        self.crawlerStatus.save()

        return
    ## DEF

    def get_api_data(self, name):
        data = {}
        data['url'] = self.crawlerStatus.source.get_url(name)
        response = requests.get(data['url'])
        soup = BeautifulSoup(response.text)
        data['time'] = soup.find('time').attrs['datetime']
        return data
    # DEF

    def add_repository(self, name, setup_scripts = None):
        if Repository.objects.filter(name='drupal/' + name, source=self.crawlerStatus.source).exists():
            LOG.info("Repository '%s' already exists" % name)
        else:
            api_data = self.get_api_data(name)

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
    # DEF

    def get_latest_sha(self, repo_name):
        url = BASE_URL.format(name = repo_name)
        response = utils.query(url)
        data = response.text
        results = re.findall(COMMIT_URL.format(sha='(\d+)'), data)
        return results[1]
    # DEF

    def download_repository(self, repo_name, sha, zip_name):
        url = BASE_URL.format(name = repo_name)
        response = utils.query(url)
        data = response.text
        download_url = re.search('https://[^ ]*?\.zip', data).group(0)

        response = utils.query(download_url)
        zip_file = open(zip_name, 'wb')
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                zip_file.write(chunk)
                zip_file.flush()
        zip_file.close()
    # DEF