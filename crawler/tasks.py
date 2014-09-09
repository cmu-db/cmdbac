from __future__ import absolute_import
from django.utils import timezone

from celery import shared_task
from crawler.models import *
from datetime import datetime
import urllib2
import subprocess
import shutil
import json
import time
import re
from django.db import IntegrityError

def query(url):
    request = urllib2.Request(url)
    token = 'aa861a6bc1c0a1cc26f708a850934310b0c23bc4'
    request.add_header('Authorization', 'token %s' % token)
    while True:
        try:
            response = urllib2.urlopen(request)
            print(url)
        except urllib2.HTTPError as e:
            continue
        return response

def process(response):
    data = json.load(response)
    for item in data['items']:
        id = item['id']
        pushed_at = item['pushed_at']
        url = item['url']
        time = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")
        repo = Repository(repo_id=id, pushed_at=time, url=url)
        try:
            repo.save()
        except IntegrityError as e:
            print(e.message)

@shared_task
def run_crawler():
    date = datetime.now().strftime("%Y-%m-%d")
    stopTime = timezone.make_aware(datetime(2014, 1, 1), timezone.get_default_timezone())
    while True:
        url = 'https://api.github.com/search/repositories?q=django+language:python+pushed:<=' + date + '&sort=updated&order=desc'
        while True:
            response = query(url)
            process(response)

            header = response.info()
            match = re.search('<(.*)>; rel="next"', str(header))
            if match == None:
                break
            else:
                url = match.group(1)
        time = Repository.objects.all().order_by("pushed_at")[0].pushed_at
        
        if(time <= stopTime):
            return 'end'
        date = time.strftime("%Y-%m-%d")
        print(date)
