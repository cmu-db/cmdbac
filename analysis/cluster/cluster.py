# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2016-07-20 01:09:51
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2016-10-20 01:06:44
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
from matplotlib.patches import Ellipse
from sklearn.preprocessing import normalize, scale
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
import string
import re

K_RANGE = xrange(1, 16)
GOOD_K_RANGE = xrange(3, 8)
# REPO_GOOD_K_RANGE = xrange(6, 7)
# TRANSACTION_GOOD_K_RANGE = xrange(4, 5)
SAMPLE = 3
RESULT_CSV = "result.csv"

def get_repo_feature_names():
    feature_names = []
    feature_names.append('repo_name')
    feature_names.append('# of tables')
    feature_names.append('# of indexes')
    feature_names.append('# of constraints')
    feature_names.append('# of foreign keys')
    feature_names.append('# of secondary indexes')
    feature_names.append('# of columns')
    feature_names.append('table coverage')
    feature_names.append('column coverage')
    feature_names.append('index coverage')
    feature_names.append('# of actions')
    feature_names.append('# of queries(total)')
    feature_names.append('# of queries(average by action)')
    feature_names.append('% of SELECT')
    feature_names.append('% of INSERT')
    feature_names.append('% of UPDATE')
    feature_names.append('% of DELETE')
    feature_names.append('# of joins')
    feature_names.append('# of read actions')
    feature_names.append('# of write actions')
    feature_names.append('# of table access(average by action)')
    feature_names.append('# of table access(average by query)')
    
    return feature_names

REPO_FEATURE_NAMES = get_repo_feature_names()

def get_transaction_feature_names():
    feature_names = []
    feature_names.append('repo_name')
    feature_names.append('# of queries')
    feature_names.append('% of SELECT')
    feature_names.append('% of INSERT')
    feature_names.append('% of UPDATE')
    feature_names.append('% of DELETE')
    feature_names.append('INSERT after SELECT')
    feature_names.append('UPDATE after SELECT')
    feature_names.append('DELETE after SELECT')
    feature_names.append('SELECT after INSERT')
    feature_names.append('SELECT after UPDATE')
    feature_names.append('SELECT after DELETE')
    feature_names.append('INSERT after DELETE')
    feature_names.append('UPDATE after INSERT')
    feature_names.append('# of writes')
    feature_names.append('# of reads')
    feature_names.append('only WRITE')
    feature_names.append('only READ')
    feature_names.append('# of joins')
    feature_names.append('# of table access')
    feature_names.append('# of primary key usage')
    feature_names.append('# of foreign key usage')
    feature_names.append('# of where clauses')
    feature_names.append('# of distinct where clauses')

    return feature_names

TRANSACTION_FEATURE_NAMES = get_transaction_feature_names()

def prepare_data():
    # prepare_repo_data()
    prepare_transaction_data()

def prepare_repo_data():
    all_data = []

    for repo in Repository.objects.filter(project_type = 1).exclude(latest_successful_attempt = None):
        repo_data = []

        repo_data.append(repo.name)

        # database information
        def get_counter(name):
            statistics = Statistic.objects.filter(attempt = repo.latest_successful_attempt).filter(description = name)
            if statistics:
                return list(statistics)[-1].count
            else:
                return 0

        repo_data.append(get_counter('num_tables'))
        num_tables = max(get_counter('num_tables'), 1)
        repo_data.append(get_counter('num_indexes'))
        repo_data.append(get_counter('num_constraints'))
        repo_data.append(get_counter('num_foreignkeys'))
        repo_data.append(get_counter('num_secondary_indexes'))
        repo_data.append(get_counter('num_columns'))
        
        repo_data.append(get_counter('table_coverage'))
        repo_data.append(get_counter('column_coverage'))
        repo_data.append(get_counter('index_coverage'))
        
        # action information
        actions = Action.objects.filter(attempt = repo.latest_successful_attempt)
        actions_count = len(actions)
        repo_data.append(actions_count)

        query_total_count = 0
        query_counters = {}
        for action in actions:
            counters = Counter.objects.filter(action = action)
            for counter in counters:
                if counter.description == 'OTHER':
                    continue
                query_counters[counter.description] = query_counters.get(counter.description, 0) + counter.count
                query_total_count += counter.count

        if query_total_count == 0:
            continue       

        repo_data.append(query_total_count)
        query_total_count = max(query_total_count, 1)
        if actions_count == 0:
            actions_count = 1
        repo_data.append(float(query_total_count) / actions_count)

        repo_data.append(float(query_counters.get('SELECT', 0)) * 100 / query_total_count)
        repo_data.append(float(query_counters.get('INSERT', 0)) * 100 / query_total_count)
        repo_data.append(float(query_counters.get('UPDATE', 0)) * 100 / query_total_count)
        repo_data.append(float(query_counters.get('DELETE', 0)) * 100 / query_total_count)

        repo_data.append(get_counter('num_joins'))
        repo_data.append(get_counter('num_read_actions'))
        repo_data.append(get_counter('num_write_actions'))
        repo_data.append(get_counter('table_access_count_action'))
        repo_data.append(float(get_counter('table_access_count_query')) / 100)
        
        assert(len(repo_data) == len(REPO_FEATURE_NAMES))

        print ' '.join(map(str, repo_data))
        # print ' '.join(map(str, zip(repo_data, REPO_FEATURE_NAMES)))

def prepare_transaction_data():
    all_data = []

    for repo in Repository.objects.exclude(latest_successful_attempt = None):
        for action in Action.objects.filter(attempt = repo.latest_successful_attempt):
            transaction = []
            
            for query in Query.objects.filter(action = action):
                if 'BEGIN' in query.content.upper() or 'START TRANSACTION' in query.content.upper() or 'SET AUTOCOMMIT=0' in query.content.upper():
                    transaction = [query.content.strip('\n')]
                elif len(transaction) > 0:
                    transaction.append(query.content.strip('\n'))

                    if 'COMMIT' in query.content.upper():
                        if len(transaction) == 2:
                            transaction = []
                            continue
                        else:
                            transaction = transaction[1:-1]

                        transaction_data = []
                        transaction_data.append(repo.name)

                        transaction_data.append(len(transaction))

                        query_type_counter = {}
                        query_types = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
                        query_with_types = []
                        for query in transaction:
                            for query_type in query_types:
                                if query_type in query:
                                    query_type_counter[query_type] = query_type_counter.get(query_type, 0) + 1
                                    query_with_types.append(query_type)
                                    break

                        for query_type in query_types:
                            transaction_data.append(query_type_counter.get(query_type, 0) * 100 / len(transaction))

                        pattern_counters = {}
                        for index, query_type in enumerate(query_with_types):
                            if index > 0:
                                last_query_type = query_with_types[index - 1]
                                feature_name = '{} after {}'.format(query_type, last_query_type)
                                if feature_name in TRANSACTION_FEATURE_NAMES:
                                    pattern_counters[feature_name] = pattern_counters.get(feature_name, 0) + 1
                        for feature_name in TRANSACTION_FEATURE_NAMES:
                            if 'after' in feature_name:
                                transaction_data.append(pattern_counters.get(feature_name, 0))
                    

                        write_count = 0
                        for keyword in ['INSERT', 'DELETE', 'UPDATE']:
                            write_count += len(re.findall(keyword, ' '.join(transaction).upper()))
                        transaction_data.append(write_count)

                        read_count = len(re.findall('SELECT', ' '.join(transaction).upper()))
                        transaction_data.append(read_count)

                        if write_count == 0 and read_count == 0:
                            continue

                        if read_count == 0:
                            transaction_data.append(1)
                        else:
                            transaction_data.append(0)

                        if write_count == 0:
                            transaction_data.append(1)
                        else:
                            transaction_data.append(0)    

                        join_count = len(re.findall('JOIN', ' '.join(transaction).upper()))
                        transaction_data.append(join_count)

                        tables = []
                        for query in transaction:
                            last_token = None
                            for token in query.split():
                                token = token.replace('"', '').replace('`', '')
                                if token in tables:
                                    tables.append(token)
                                elif last_token == 'FROM' and '(' not in token and ')' not in token:
                                    tables.append(token)
                                last_token = token
                        transaction_data.append(len(tables))

                        if len(tables) == 0:
                            continue

                        key_column_usage_informations = Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'key_column_usage')
                        constraint_informations = Information.objects.filter(attempt = repo.latest_successful_attempt).filter(name = 'constraints')
                        constraint_map = {}
                        if len(key_column_usage_informations) > 0 and len(constraint_informations) > 0:
                            if repo.latest_successful_attempt.database.name == 'PostgreSQL':
                                regex = '(\(.*?\))[,\]]'
                            elif repo.latest_successful_attempt.database.name == 'MySQL':
                                regex = '(\(.*?\))[,\)]'
                            
                            merge_map = {}
                            key_column_usage_information = key_column_usage_informations[0]
                            for column in re.findall(regex, key_column_usage_information.description):
                                cells = column.split(',')
                                constraint_name = str(cells[2]).replace("'", "").strip()
                                table_name = str(cells[5]).replace("'", "").strip()
                                column_name = str(cells[6]).replace("'", "").strip()
                                merge_map_key = table_name + '.' + constraint_name 
                                if merge_map_key in merge_map:
                                    merge_map[merge_map_key].append(column_name)
                                else:
                                    merge_map[merge_map_key] = [column_name]

                            constraint_information = constraint_informations[0]
                            for column in re.findall(regex, constraint_information.description):
                                cells = column.split(',')
                                constraint_name = str(cells[2]).replace("'", "").strip()
                                if repo.latest_successful_attempt.database.name == 'PostgreSQL':
                                    table_name = str(cells[5]).replace("'", "").strip()
                                    constraint_type = str(cells[6]).replace("'", "").strip()
                                elif repo.latest_successful_attempt.database.name == 'MySQL':
                                    table_name = str(cells[4]).replace("'", "").strip()
                                    constraint_type = str(cells[5])[:-1].replace("'", "").strip()
                                merge_map_key =  table_name + '.' + constraint_name
                                if merge_map_key in merge_map:
                                    for column_name in merge_map[merge_map_key]:
                                        constraint_map[table_name + '.' + column_name] = constraint_type
                                        constraint_map[column_name] = constraint_type

                        keys_usage = {}
                        for query in transaction:
                            for token in query.split():
                                token = token.replace('"', '').replace('`', '')
                                if token in constraint_map:
                                    keys_usage[constraint_map[token].upper()] = keys_usage.get(constraint_map[token], 0) + 1
                        transaction_data.append(keys_usage.get('PRIMARY KEY', 0))
                        transaction_data.append(keys_usage.get('FOREIGN KEY', 0))

                        where_clauses = set()
                        where_clauses_count = 0
                        for query in transaction:
                            where_pos = query.find('WHERE')
                            if where_pos != -1:
                                where_clause = query[where_pos + 5:].strip()
                                if where_clause != None:
                                    where_clauses_count += 1
                                    where_clauses.add(where_clause)
                        transaction_data.append(where_clauses_count)
                        transaction_data.append(len(where_clauses))

                        assert(len(transaction_data) == len(TRANSACTION_FEATURE_NAMES))

                        # print transaction

                        print ' '.join(map(str, transaction_data))

                        transaction = []
                        # print ' '.join(map(str, zip(transaction_data, TRANSACTION_FEATURE_NAMES)))

def read_data(category):
    if category == 'repo':
        return read_repo_data()
    elif category == 'txn':
        return read_transaction_data()

def read_repo_data():
    repo_names = []
    all_data = []

    line = sys.stdin.readline()
    while line:
        repo_data = map(float, line.split()[1:])
        all_data.append(repo_data)
        repo_names.append(line.split()[0])

        assert(len(repo_data) + 1 == len(REPO_FEATURE_NAMES))

        line = sys.stdin.readline()
    
    return repo_names, all_data

def read_transaction_data():
    transaction_names = []
    all_data = []

    line = sys.stdin.readline()
    while line:
        transaction_data = map(float, line.split()[1:])
        all_data.append(transaction_data)
        transaction_names.append(line.split()[0])
    
        assert(len(transaction_data) + 1 == len(TRANSACTION_FEATURE_NAMES))

        line = sys.stdin.readline()

    return transaction_names, all_data

# Reference: https://github.com/dvanaken/ottertune/blob/master/analysis/preprocessing.py
class Bin(object):
    
    def __init__(self, bin_start, axis=None):
        if axis is not None and \
                axis != 1 and axis != 0:
            raise NotImplementedError("Axis={} is not yet implemented"
                                      .format(axis))
        self.deciles_ = None
        self.bin_start_ = bin_start
        self.axis_ = axis
    
    def fit(self, matrix):
        if self.axis_ is None:
            self.deciles_ = get_deciles(matrix, self.axis_)
        elif self.axis_ == 0: # Bin columns
            self.deciles_ = []
            for col in matrix.T:
                self.deciles_.append(get_deciles(col, axis=None))
        elif self.axis_ == 1: # Bin rows
            self.deciles_ = []
            for row in matrix:
                self.deciles_.append(get_deciles(row, axis=None))
        return self

    def transform(self, matrix, copy=True):
        assert self.deciles_ is not None
        if self.axis_ is None:
            res = bin_by_decile(matrix, self.deciles_,
                                 self.bin_start_, self.axis_)
        elif self.axis_ == 0: # Transform columns
            columns = []
            for col, decile in zip(matrix.T, self.deciles_):
                columns.append(bin_by_decile(col, decile,
                                             self.bin_start_, axis=None))
            res = np.vstack(columns).T
        elif self.axis_ == 1: # Transform rows
            rows = []
            for row, decile in zip(matrix, self.deciles_):
                rows.append(bin_by_decile(row, decile,
                                          self.bin_start_, axis=None))
            res = np.vstack(rows)
        assert res.shape == matrix.shape
        return res

def get_deciles(matrix, axis=None):
    if axis is not None:
        raise NotImplementedError("Axis is not yet implemented")
    
    assert matrix.ndim > 0
    assert matrix.size > 0
    
    decile_range = np.arange(10,101,10)
    deciles = np.percentile(matrix, decile_range, axis=axis)
    deciles[-1] = np.Inf
    return deciles

def bin_by_decile(matrix, deciles, bin_start, axis=None):
    if axis is not None:
        raise NotImplementedError("Axis is not yet implemented")
    
    assert matrix.ndim > 0
    assert matrix.size > 0
    assert deciles is not None
    assert len(deciles) == 10
    
    binned_matrix = np.zeros_like(matrix)
    for i in range(10)[::-1]:
        decile = deciles[i]
        binned_matrix[matrix <= decile] = i + bin_start
    
    return binned_matrix

def kmeans(repo, data):
    n = len(data)
    bin_ = Bin(0, 0)
    # processed_data = scale(data)
    data = np.array(data)
    bin_.fit(data)
    processed_data = bin_.transform(data)

    output = open(RESULT_CSV, 'w')
    # output.write(','.join(REPO_FEATURE_NAMES[1:]) + '\n')
    output.write(','.join(TRANSACTION_FEATURE_NAMES[1:]) + '\n')

    for k in GOOD_K_RANGE:
        kmeans = KMeans(init='k-means++', n_clusters=k)
        kmeans.fit(processed_data)
        distances = kmeans.transform(processed_data)
        points = {}
        mean_centroids = {}

        labels_map = {}
        for i, x in enumerate(kmeans.cluster_centers_[:, 0].argsort()):
            labels_map[x] = string.uppercase[i]

        labels_cnt = {}
        for i in xrange(n):
            #print 'Data: ', data[i], ' Label: ', kmeans.labels_[i]
            label = labels_map[kmeans.labels_[i]]
            labels_cnt[label] = labels_cnt.get(label, 0) + 1
            if label not in points:
                points[label] = []
            points[label].append((distances[i][kmeans.labels_[i]], i))
            if label not in mean_centroids:
                mean_centroids[label] = data[i]
            for index, value in enumerate(data[i]):
                mean_centroids[label][index] += value
            
        for label in xrange(k):
            new_label = labels_map[label]
            print 'Cluster: {}'.format(new_label)
            # print zip(REPO_FEATURE_NAMES[1:], map(lambda x: round(x, 2), kmeans.cluster_centers_[label]))
            print zip(TRANSACTION_FEATURE_NAMES[1:], map(lambda x: round(x, 2), kmeans.cluster_centers_[label]))
            
            
            # output.write(str(label) + ',' + ','.join(map(lambda x: str(round(x, 2)), kmeans.cluster_centers_[label])) + '\n')
            # points[label] = sorted(points[label])

            mean_centroids[new_label] = map(lambda x: x / labels_cnt[new_label], mean_centroids[new_label])
            output.write(str(new_label) + ',' + ','.join(map(lambda x: str(round(x, 2)), mean_centroids[new_label])) + '\n')
            
            if 0:
                for i in xrange(min(len(points[label]), SAMPLE)):
                    print 'Sample: {}'.format(i)
                    print points[label][i]
                    print repo[points[label][i][1]]
                    # print zip(REPO_FEATURE_NAMES[1:], processed_data[points[label][i][1]])
                    print zip(TRANSACTION_FEATURE_NAMES[1:], processed_data[points[label][i][1]])
                    # output.write(str(label) + '_' + str(i) + ',' + ','.join(map(lambda x: str(round(x, 2)), data[points[label][i][1]])) + '\n')
                    # output.write(str(label) + '_' + str(i) + ',' + ','.join(map(lambda x: str(round(x, 2)), processed_data[points[label][i][1]])) + '\n')

            print '-' * 20

        print k, labels_cnt

        output.close()

def kmeans_pca(data):
    import seaborn as sns
    
    n = len(data)
    bin_ = Bin(0, 0)
    # processed_data = scale(data)
    data = np.array(data)
    bin_.fit(data)
    processed_data = bin_.transform(data)
    pca = PCA(n_components=5).fit(processed_data)
    reduced_data = pca.transform(processed_data)[:, :2]    

    for k in GOOD_K_RANGE:
        kmeans = KMeans(init='k-means++', n_clusters=k)
        kmeans.fit(reduced_data)

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)

        x_min, x_max = reduced_data[:, 0].min() - 1, reduced_data[:, 0].max() + 1
        y_min, y_max = reduced_data[:, 1].min() - 1, reduced_data[:, 1].max() + 1
        
        colors = sns.color_palette("muted")
        for k, col in zip(range(k), colors):
            my_members = kmeans.labels_ == k
            cluster_center = kmeans.cluster_centers_[k]
            ax.plot(reduced_data[my_members, 0], reduced_data[my_members, 1], 'w',
                markerfacecolor=col, marker='.', markersize=5)
            ax.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col,
                markeredgecolor='k', markersize=8)
        centroids = kmeans.cluster_centers_[kmeans.cluster_centers_[:, 0].argsort()]
        for label, x, y in zip(string.uppercase[:k + 1], centroids[:, 0], centroids[:, 1]):
            plt.annotate(label, xy = (x, y), xytext = (-20, 20),
                textcoords = 'offset points', ha = 'right', va = 'bottom',
                bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
                arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))

        ax.set_title('KMeans')
        plt.xlim(x_min, x_max)
        plt.ylim(y_min, y_max)
        plt.xticks(())
        plt.yticks(())
        
        labels_map = {}
        for i, x in enumerate(kmeans.cluster_centers_[:, 0].argsort()):
            labels_map[x] = string.uppercase[i]
        labels_cnt = {}
        for label in kmeans.labels_:
            labels_cnt[labels_map[label]] = labels_cnt.get(labels_map[label], 0) + 1
        print labels_cnt
        labels_percentage = {}
        for label, count in labels_cnt.iteritems():
            labels_percentage[label] = float(count) * 100 / sum(labels_cnt.values())
        print labels_percentage
        
        fig.savefig('kmeans-pca-{}.pdf'.format(k))

def plot_point_cov(points, nstd=2, ax=None, **kwargs):
    """
    Plots an `nstd` sigma ellipse based on the mean and covariance of a point
    "cloud" (points, an Nx2 array).
    Parameters
    ----------
        points : An Nx2 array of the data points.
        nstd : The radius of the ellipse in numbers of standard deviations.
            Defaults to 2 standard deviations.
        ax : The axis that the ellipse will be plotted on. Defaults to the 
            current axis.
        Additional keyword arguments are pass on to the ellipse patch.
    Returns
    -------
        A matplotlib ellipse artist
    """
    pos = points.mean(axis=0)
    cov = np.cov(points, rowvar=False)
    return plot_cov_ellipse(cov, pos, nstd, ax, **kwargs)

def plot_cov_ellipse(cov, pos, nstd=2, ax=None, **kwargs):
    """
    Plots an `nstd` sigma error ellipse based on the specified covariance
    matrix (`cov`). Additional keyword arguments are passed on to the 
    ellipse patch artist.
    Parameters
    ----------
        cov : The 2x2 covariance matrix to base the ellipse on
        pos : The location of the center of the ellipse. Expects a 2-element
            sequence of [x0, y0].
        nstd : The radius of the ellipse in numbers of standard deviations.
            Defaults to 2 standard deviations.
        ax : The axis that the ellipse will be plotted on. Defaults to the 
            current axis.
        Additional keyword arguments are pass on to the ellipse patch.
    Returns
    -------
        A matplotlib ellipse artist
    """
    def eigsorted(cov):
        vals, vecs = np.linalg.eigh(cov)
        order = vals.argsort()[::-1]
        return vals[order], vecs[:,order]

    if ax is None:
        ax = plt.gca()

    vals, vecs = eigsorted(cov)
    theta = np.degrees(np.arctan2(*vecs[:,0][::-1]))

    # Width and height are "full" widths, not radius
    width, height = 2 * nstd * np.sqrt(vals)
    ellip = Ellipse(xy=pos, width=width, height=height, angle=theta, **kwargs)

    ax.add_artist(ellip)
    return ellip,pos,width,height

def kmeans_pca_ellipse(data):
    import seaborn as sns
    
    n = len(data)
    bin_ = Bin(0, 0)
    # processed_data = scale(data)
    data = np.array(data)
    bin_.fit(data)
    processed_data = bin_.transform(data)
    pca = PCA(n_components=5).fit(processed_data)
    reduced_data = pca.transform(processed_data)[:, :2]    

    for k in GOOD_K_RANGE:
        kmeans = KMeans(init='k-means++', n_clusters=k)
        kmeans.fit(reduced_data)

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)

        x_min, x_max = reduced_data[:, 0].min() - 1, reduced_data[:, 0].max() + 1
        y_min, y_max = reduced_data[:, 1].min() - 1, reduced_data[:, 1].max() + 1
        
        colors = sns.color_palette("muted")
        for i, col in zip(range(k), colors):
            my_members = kmeans.labels_ == i
            plt.plot(reduced_data[my_members, 0], reduced_data[my_members, 1], '.', markersize=3, color = col)
            plot_point_cov(reduced_data[my_members], ax = ax, color = 'white')

        centroids = kmeans.cluster_centers_[kmeans.cluster_centers_[:, 0].argsort()]
        for label, x, y in zip(string.uppercase[:k + 1], centroids[:, 0], centroids[:, 1]):
            plt.annotate(label, xy = (x, y), xytext = (0, 0),
                textcoords = 'offset points', ha = 'right', va = 'bottom',
                bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5))

        ax.set_title('KMeans')
        plt.xlim(x_min, x_max)
        plt.ylim(y_min, y_max)
        plt.xticks(())
        plt.yticks(())
        
        labels_map = {}
        for i, x in enumerate(kmeans.cluster_centers_[:, 0].argsort()):
            labels_map[x] = string.uppercase[i]
        labels_cnt = {}
        for label in kmeans.labels_:
            labels_cnt[labels_map[label]] = labels_cnt.get(labels_map[label], 0) + 1
        print labels_cnt
        labels_percentage = {}
        for label, count in labels_cnt.iteritems():
            labels_percentage[label] = float(count) * 100 / sum(labels_cnt.values())
        print labels_percentage
        
        fig.savefig('kmeans-pca.pdf')

def pca_dbscan(category, data):
    n = len(data)
    bin_ = Bin(0, 0)
    # processed_data = scale(data)
    data = np.array(data)
    bin_.fit(data)
    processed_data = bin_.transform(data)
    pca = PCA(n_components=5).fit(processed_data)
    reduced_data = pca.transform(processed_data)[:, :2]

    output = open(RESULT_CSV, 'w')
    if category == 'repo':
        output.write(','.join(REPO_FEATURE_NAMES) + '\n')
    elif category == 'txn':
        output.write(','.join(TRANSACTION_FEATURE_NAMES) + '\n')

    DJANGO_PAR = ([1.9], [70])
    RUBY_PAR = ([1.8], [20])
    TXN_PAR = ([1.5], [40])

    DBSCAN_PAR = DJANGO_PAR

    # for eps, min_samples in RUBY_PAR:
    for eps in DBSCAN_PAR[0]:
        for min_samples in DBSCAN_PAR[1]:
            db = DBSCAN(eps=eps, min_samples=min_samples).fit(reduced_data)
            core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
            core_samples_mask[db.core_sample_indices_] = True
            labels = db.labels_
            n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)

            print('Estimated number of clusters: %d' % n_clusters_)

            fig = plt.figure()
            plt.clf()
            # x_min, x_max = reduced_data[:, 0].min() - 1, reduced_data[:, 0].max() + 1
            # y_min, y_max = reduced_data[:, 1].min() - 1, reduced_data[:, 1].max() + 1

            unique_labels = set(labels)

            if len(unique_labels) > 7:
                continue

            labels_map = {}
            for i, x in enumerate(unique_labels):
                labels_map[x] = string.uppercase[i]
            labels_cnt = {}
            for label in labels:
                labels_cnt[labels_map[label]] = labels_cnt.get(labels_map[label], 0) + 1
            print labels_cnt
            labels_percentage = {}
            for label, count in labels_cnt.iteritems():
                labels_percentage[label] = float(count) * 100 / sum(labels_cnt.values())
            print labels_percentage

            colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
            for k, col in zip(unique_labels, colors):
                if k == -1:
                    # Black used for noise.
                    col = 'k'
                
                class_member_mask = (labels == k)

                xy = reduced_data[class_member_mask & core_samples_mask]
                plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=col,
                         markeredgecolor='k', markersize=10)

                label = labels_map[k]
                annotation = False
                if k != -1:
                    plt.annotate(label, xy = (xy[0, 0], xy[0, 1]), xytext = (0, 0),
                        textcoords = 'offset points', ha = 'right', va = 'bottom',
                        bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5))
                
                xy = reduced_data[class_member_mask & ~core_samples_mask]
                plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=col,
                         markeredgecolor='k', markersize=4)

            for k in unique_labels:
                if k == -1:
                    continue
                class_member_mask = (labels == k)
                centroid = map(lambda x: round(x, 2), data[class_member_mask].mean(axis = 0))
                bin_centroid = map(lambda x: round(x, 2), processed_data[class_member_mask].mean(axis = 0))
                new_label = labels_map[k]
                output.write(str(new_label) + ',' + ','.join(map(str, centroid)) + '\n')
                # output.write(str(new_label) + ',' + ','.join(map(str, bin_centroid)) + '\n')

            plt.xticks(())
            plt.yticks(())
            
            fig.savefig('db-pca.pdf'.format(eps, min_samples))

def kmeans_elbow(data):
    bin_ = Bin(0, 0)
    # processed_data = scale(data)
    data = np.array(data)
    bin_.fit(data)
    processed_data = bin_.transform(data)
    # processed_data = scale(data)
    
    inertias = []
    for k in K_RANGE:
        kmeans = KMeans(init='k-means++', n_clusters=k)
        kmeans.fit(processed_data)
        inertias.append(kmeans.inertia_)

    fig = plt.figure()
    plt.scatter(K_RANGE, inertias)
    plt.plot(K_RANGE, inertias)
    fig.savefig('kmeans-elbow.png')
        
def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'prepare':
            prepare_data()
        else:
            category = None
            if len(sys.argv) > 2:
                category = sys.argv[2]
            repo, data = read_data(category)
            if command == 'kmeans':
                kmeans(repo, data)
            elif command == 'pca':
                kmeans_pca(data)
            elif command == 'pca2':
                kmeans_pca_ellipse(data)
            elif command == 'pca3':
                pca_dbscan(category, data)
            elif command == 'elbow':
                kmeans_elbow(data)

if __name__ == "__main__":
    main()