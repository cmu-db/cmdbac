# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2016-07-20 01:09:51
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2016-07-20 23:04:01
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from utils import filter_repository, dump_all_stats

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *

import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

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
    for k in k_range:
        # kmeans_var = KMeans(n_clusters = k).fit(data)

        reduced_data = PCA(n_components=2).fit_transform(data)
        kmeans = KMeans(init='k-means++', n_clusters=k)
        kmeans.fit(reduced_data)

        # Step size of the mesh. Decrease to increase the quality of the VQ.
        h = .02     # point in the mesh [x_min, m_max]x[y_min, y_max].

        # Plot the decision boundary. For that, we will assign a color to each
        x_min, x_max = reduced_data[:, 0].min() - 1, reduced_data[:, 0].max() + 1
        y_min, y_max = reduced_data[:, 1].min() - 1, reduced_data[:, 1].max() + 1
        xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))

        # Obtain labels for each point in mesh. Use last trained model.
        Z = kmeans.predict(np.c_[xx.ravel(), yy.ravel()])

        # Put the result into a color plot
        Z = Z.reshape(xx.shape)
        plt.figure(1)
        plt.clf()
        plt.imshow(Z, interpolation='nearest',
                   extent=(xx.min(), xx.max(), yy.min(), yy.max()),
                   cmap=plt.cm.Paired,
                   aspect='auto', origin='lower')

        plt.plot(reduced_data[:, 0], reduced_data[:, 1], 'k.', markersize=2)
        # Plot the centroids as a white X
        centroids = kmeans.cluster_centers_
        plt.scatter(centroids[:, 0], centroids[:, 1],
                    marker='x', s=169, linewidths=3,
                    color='w', zorder=10)
        plt.title('K-means clustering on the digits dataset (PCA-reduced data)\n'
                  'Centroids are marked with white cross')
        plt.xlim(x_min, x_max)
        plt.ylim(y_min, y_max)
        plt.xticks(())
        plt.yticks(())
        plt.show()

    print kmeans_var
    
if __name__ == "__main__":
    main()