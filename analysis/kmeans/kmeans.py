# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2016-07-20 01:09:51
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2016-07-20 20:52:32
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from utils import filter_repository, dump_all_stats

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *
from sklearn.cluster import KMeans

def prepare_data():
    all_data = []

    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        repo_data = []

        # basic information
        repo_data.append(repo.size)
        repo_data.append(repo.forks_count)
        repo_data.append(repo.commits_count)
        repo_data.append(repo.contributors_count)
        # repo_data.append(repo.stargazers_count)
        # repo_data.append(repo.open_issues_count)
        # repo_data.append(repo.network_count)
        # repo_data.append(repo.subscribers_count)
        # repo_data.append(repo.branches_count)
        # repo_data.append(repo.subscribers_count)
        # repo_data.append(repo.releases_count)

        def get_counter(name):
            statistics = Statistic.objects.filter(attempt = repo.latest_successful_attempt).filter(description = name)
            if statistics:
                return list(statistics)[-1].count
            else:
                return 0
        repo_data.append(get_counter('num_tables'))
        repo_data.append(get_counter('num_indexes'))
        repo_data.append(get_counter('num_constraints'))
        repo_data.append(get_counter('num_foreignkeys'))
        # repo_data.append(get_counter('num_transactions'))

        actions = Action.objects.filter(attempt = repo.latest_successful_attempt)
        repo_data.append(len(actions))

        all_data.append(repo_data)

    return all_data
        
def main():
    data = prepare_data()

    k_range = (1, 5)
    kmeans_var = [KMeans(n_clusters = k).fit(data) for k in k_range]
    print kmeans_var
    
if __name__ == "__main__":
    main()