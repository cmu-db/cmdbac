import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import time
import re
import urllib
import urllib2
import logging
import urlparse
from string import Template
from bs4 import BeautifulSoup
from datetime import datetime
from string import Template
import json

from basecrawler import BaseCrawler
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
## GITHUB CONFIGURATION
## =====================================================================

BASE_URL = "https://api.github.com/search/code?utf8=%E2%9C%93&q=${query}+" + \
           "filename%3A${filename}+" + \
           "size%3A${size}&" + \
           "type=Code&ref=searchresults"
GITHUB_HOST = 'https://github.com/'
API_GITHUB_REPO = 'https://api.github.com/repos/'
API_GITHUB_SLEEP = 4 # seconds
GITHUB_API_COMMITS_URL = Template('https://api.github.com/repos/${name}/commits')
GITHUB_DOWNLOAD_URL_TEMPLATE = Template('https://github.com/${name}/archive/${sha}.zip')

## =====================================================================
## GITHUB CRAWLER
## =====================================================================
class GitHubCrawler(BaseCrawler):
    def __init__(self, crawlerStatus, auth):
        BaseCrawler.__init__(self, crawlerStatus, auth)

        self.template = Template(BASE_URL)
    ## DEF

    def next_url(self):
        # compute what the next page we want to load
        args = {
            "query": urllib.urlencode({
                'q': self.crawlerStatus.query})[2:] if self.crawlerStatus.query != '' else '',
            "filename": self.crawlerStatus.project_type.filename
        }

        if self.crawlerStatus.cur_size == self.crawlerStatus.max_size:
            args["size"] = '>'+str(self.crawlerStatus.cur_size)
            self.crawlerStatus.cur_size = self.crawlerStatus.min_size
        else:
            args["size"] = self.crawlerStatus.cur_size
            self.crawlerStatus.cur_size = self.crawlerStatus.cur_size + 1

        print self.template.substitute(args)
        return self.template.substitute(args)
    ## DEF

    def github_query(self, url):
        return utils.query(url, auth = self.auth)

    def search(self):
        # Load and parse!
        response = self.github_query(self.next_url())
        response_json = json.loads(response.text)

        total_count = response_json["total_count"]
        LOG.info("Found %d repositories" % total_count)

        # Pick through the results and find repos
        repositories = map(lambda item: item['repository'], response_json['items'])
        for repo in repositories:
            name = repo['full_name']
            try:
                self.add_repository(name)
            except Exception, e:
                LOG.exception(e)
            # Sleep for a little bit to prevent us from getting blocked
            time.sleep(API_GITHUB_SLEEP)
        ## FOR

        # Make sure we update our crawler status
        LOG.info("Updating status for %s" % self.crawlerStatus)
        self.crawlerStatus.save()

        return
    ## DEF

    def get_api_data(self, name):
        response = self.github_query(urlparse.urljoin(API_GITHUB_REPO, name))
        data = response.json()
        return data
    ## DEF

    def get_webpage_data(self, name):
        data = {}
        response = self.github_query(urlparse.urljoin(GITHUB_HOST, name))
        soup = BeautifulSoup(response.text)
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

    def add_repository(self, name, setup_scripts = None):
        if Repository.objects.filter(name=name, source=self.crawlerStatus.source).exists():
            LOG.info("Repository '%s' already exists" % name)
        else:
            api_data = self.get_api_data(name)
            if api_data.get('message', '') == 'Not Found':
                raise Exception('Not Found')

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
            repo.setup_scripts = setup_scripts
            repo.save()
            LOG.info("Successfully created new repository '%s' [%d]" % (repo, repo.id))
        ## IF
    ## DEF

    def get_latest_sha(self, repo_name):
        url = GITHUB_API_COMMITS_URL.substitute(name=repo_name)
        response = self.github_query(url)
        data = response.json()
        time.sleep(1)
        return data[0]['sha']
    # DEF

    def download_repository(self, repo_name, sha, zip_name):
        try:
            with open(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "secrets", "secrets.json"), 'r') as auth_file:
                auth = json.load(auth_file)
        except:
            auth = None
        url = GITHUB_DOWNLOAD_URL_TEMPLATE.substitute(name=repo_name, sha=sha)
        response = self.github_query(url)
        zip_file = open(zip_name, 'wb')
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                zip_file.write(chunk)
                zip_file.flush()
        zip_file.close()
    # DEF