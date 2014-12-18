import os
import time
from url import URL
from utils import Utils
from string import Template
from bs4 import BeautifulSoup
from constants import Constants
import json
from datetime import datetime
import re
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")

import django
django.setup()


from crawler.models import *
class Crawler:
    def __init__(self, repo_type):
        self.name = repo_type.name
        self.template = Template("https://github.com/search?utf8=%E2%9C%93&q=" + repo_type.filename + "+in%3Apath+filename%3A" + repo_type.filename + "+size%3A${size}&type=Code&ref=searchresults")
# model file less than min_size don't use database
        self.min_size = repo_type.min_size
# less then 1000 files larger than threshold_size
        self.max_size = repo_type.max_size
        self.cur_size = repo_type.cur_size

    def get_webpage_data(self, full_name):
        data = {}
        url = URL(os.path.join(Constants.GITHUB_HOST, full_name))
        response = url.query()
        soup = BeautifulSoup(response.read())
        numbers = soup.find_all(class_='num text-emphasized')
        try:
            data['commits_count'] = int(re.sub("\D", "", numbers[0].string))
        except:
            data['commits_count'] = 0
        try:
            data['branches_count'] = int(re.sub("\D", "", numbers[1].string))
        except:
            data['branches_count'] = 0
        try:
            data['releases_count'] = int(re.sub("\D", "", numbers[2].string))
        except:
            data['releases_count'] = 0
        try:
            data['contributors_count'] = int(re.sub("\D", "", numbers[3].string))
        except:
            data['contributors_count'] = 0
        return data


    def get_api_data(self, full_name):
        url = URL(os.path.join(Constants.API_GITHUB_REPO, full_name))
        reponse = url.query()
        data = json.load(reponse)
        return data

    def crawl(self):
        if self.cur_size == self.max_size:
            url = URL(self.template.substitue(size='>'+str(self.cur_size)))
            self.cur_size = slef.min_size
        else:
            url = URL(self.template.substitute(size=self.cur_size))
            self.cur_size = self.cur_size + 1

        while True:
            response = url.query()
            soup = BeautifulSoup(response.read())
            titles = soup.find_all(class_='title')
            for title in titles:
                full_name = title.contents[1].string
                if Repository.objects.filter(full_name=full_name).exists():
                    print("repository already exist: " + full_name)
                else:
                    print("found new repository " + full_name + ". call github api")
                    api_data = self.get_api_data(full_name)
                    webpage_data = self.get_webpage_data(full_name)
                    repo = Repository()
                    repo.full_name = full_name
                    repo.repo_type = Type(name=self.name)
                    repo.last_attempt = None
                    repo.private = api_data['private']
                    repo.description = Utils.none2empty(api_data['description'])
                    repo.fork = api_data['fork']
                    repo.created_at = datetime.strptime(api_data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                    repo.updated_at = datetime.strptime(api_data['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
                    repo.pushed_at = datetime.strptime(api_data['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
                    repo.homepage = Utils.none2empty(api_data['homepage'])
                    repo.size = api_data['size']
                    repo.stargazers_count = api_data['stargazers_count']
                    repo.watchers_count = api_data['watchers_count']
                    repo.language = Utils.none2empty(api_data['language'])
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
                time.sleep(1)
            next_page = soup.find(class_='next_page')
            if not next_page or not next_page.has_attr('href'):
                return
            url = URL(Constants.GITHUB_HOST + next_page['href'])
            time.sleep(1)

    def save(self):
        repo_type = Type.objects.get(name=self.name)
        repo_type.cur_size = self.cur_size
        repo_type.save()

#def main():
#    while True:
#        repo_types = Type.objects.all()
#        for repo_type in repo_types:
#            crawler = Crawler(repo_type)
#            crawler.crawl()
#            crawler.save()
#    #        if crawler.repo_type.cur_size == crawler.repo_type.max_size:
#                
#if __name__ == '__main__':
#    main()
