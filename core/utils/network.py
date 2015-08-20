import urllib2
from string import Template
import json
import time
import shutil

def query(url):
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    header = response.info().dict;
    return response

GITHUB_DOWNLOAD_URL_TEMPLATE = Template('https://github.com/${name}/archive/${sha}.zip')

def download(attempt, zip_name):
    url = GITHUB_DOWNLOAD_URL_TEMPLATE.substitute(name=attempt.repo.name, sha=attempt.sha)
    response = query(url)
    zip_file = open(zip_name, 'wb')
    shutil.copyfileobj(response.fp, zip_file)
    zip_file.close()

GITHUB_API_COMMITS_URL = Template('https://api.github.com/repos/${name}/commits')

def get_latest_sha(repo):
    url = GITHUB_API_COMMITS_URL.substitute(name=repo.name)
    try:
        response = query(url)
    except:
        print traceback.print_exc()
        return
    data = json.load(response)
    time.sleep(1) 
    return data[0]['sha']