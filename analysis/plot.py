#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: zeyuanxy
# @Date:   2016-03-21 01:52:14
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2016-03-28 23:28:34
import sys
import os
import numpy as np 
import matplotlib.pyplot as plt

FIG_DIRECTORY = os.path.join(os.path.dirname(__file__), 'fig')

def plot_numeric_histogram(directory, csv_file, output_directory, bins = 10, max_value = None):
    stats = {}
    with open(os.path.join(directory, csv_file), 'r') as f:
        description = f.readline()
        for line in f.readlines():
            cells = line.strip().split(',')
            label = cells[0]
            value = int(cells[1])
            if label not in stats:
                stats[label] = []
            stats[label].append(value)
    labels = []
    points = []
    for label, values in stats.iteritems():
        labels.append(label)
        points.append(values)

    plt.clf()
    fig = plt.Figure()
    fig.set_canvas(plt.gcf().canvas)
    plt.figure(1, figsize=(6,6))
    if max_value != None:
        plt.hist(points, bins, range=(0, max_value), histtype='barstacked', label = labels)
    else:
        plt.hist(points, bins, histtype='barstacked', label = labels)
    if len(labels) > 1:
        plt.legend(loc='upper right', bbox_to_anchor = (1.0, 1.0), ncol=1)
    plt.ylabel('num_repos')
    name = csv_file.split('.')[0]
    plt.xlabel(name)
    fig.savefig(os.path.join(output_directory, name + '.pdf'))

def plot_pie_chart(directory, csv_file, output_directory, min_percentage = 0.05):
    stats = {'others': 0}
    total = .0
    with open(os.path.join(directory, csv_file), 'r') as f:
        description = f.readline()
        for line in f.readlines():
            cells = line.split(',')
            stats[cells[0]] = float(cells[1])
            total += float(cells[1])

    labels = []
    quants = []
    for label, quant in stats.iteritems():
        if label == 'others':
            continue
        if quant < min_percentage * total:
            stats['others'] = stats['others'] + quant
        else:
            labels.append(label)
            quants.append(quant)
    if stats['others'] > 0:
        labels.append('others')
        quants.append(stats['others'])

    plt.clf()
    fig = plt.Figure()
    fig.set_canvas(plt.gcf().canvas)
    plt.figure(1, figsize=(6,6))
    plt.pie(quants, labels=labels, autopct='%1.2f%%', pctdistance=0.8, shadow=True)
    name = csv_file.split('.')[0]
    plt.title(name)
    fig.savefig(os.path.join(output_directory, name + '.pdf'))

def plot_table(directory, csv_file, output_directory):
    # prepare data
    stats = {}
    row_labels = []
    col_labels = []
    with open(os.path.join(directory, csv_file), 'r') as f:
        description = f.readline()
        for line in f.readlines():
            cells = line.split(',')
            row_label = cells[0]
            if row_label not in row_labels:
                row_labels.append(row_label)
            if row_label not in stats:
                stats[row_label] = {}
            col_label = cells[1]
            if col_label not in col_labels:
                col_labels.append(col_label)
            value = int(cells[2])
            stats[row_label][col_label] = value
    data = []
    for row_label in row_labels:
        data.append([])
        for col_label in col_labels:
            if row_label not in stats:
                data[-1].append(0)
                continue
            if col_label not in stats[row_label]:
                data[-1].append(0)
                continue
            data[-1].append(stats[row_label][col_label])

    # prepare figure
    plt.clf()
    fig = plt.Figure()
    fig.set_canvas(plt.gcf().canvas)
    plt.figure(1, figsize=(6,6))

    # bar
    colors = plt.cm.BuPu(np.linspace(0, 0.5, len(row_labels)))
    n_rows = len(data)
    index = np.arange(len(col_labels)) + 0.3
    bar_width = 0.4
    y_offset = np.array([0.0] * len(col_labels))
    for row in range(len(row_labels)):
        plt.bar(index, data[row], bar_width, bottom=y_offset, color=colors[row])
        y_offset = y_offset + data[row]
    colors = colors[::-1]

    # make room for the table
    plt.subplots_adjust(left=0.2, bottom=0.3)

    # table 
    plt.table(cellText = data, rowLabels = row_labels, rowColours = colors, colLabels = col_labels)
    name = csv_file.split('.')[0]
    plt.title(name)
    plt.xticks([])
    fig.savefig(os.path.join(output_directory, name + '.pdf'))

def plot_tables(directory):
    output_directory = os.path.join(FIG_DIRECTORY, 'tables')

    # active
    plot_histogram(directory, 'num_tables.csv', output_directory, max_value = 100)
    plot_histogram(directory, 'num_indexes.csv', output_directory, max_value = 100)
    plot_histogram(directory, 'num_foreignkeys.csv', output_directory)
    plot_pie_chart(directory, 'column_nullable.csv', output_directory)
    plot_pie_chart(directory, 'column_types.csv', output_directory)
    
    # deprecated
    # TODO : plot_histogram(directory, 'num_constraints.csv', output_directory)
    # TODO : plot_pie_chart(directory, 'constraint_types.csv', output_directory)

def plot_queries(directory):
    output_directory = os.path.join(FIG_DIRECTORY, 'queries')

    # active
    plot_table(directory, 'query.csv', output_directory)
    plot_histogram(directory, 'table_coverage.csv', output_directory)
    plot_histogram(directory, 'column_coverage.csv', output_directory)
    plot_histogram(directory, 'index_coverage.csv', output_directory)

    # working
    # plot_pie_chart(directory, 'join.csv', output_directory, 0)
    # plot_pie_chart(directory, 'logical.csv', output_directory, 0)
    # plot_pie_chart(directory, 'scan.csv', output_directory, 0.01)
    # plot_pie_chart(directory, 'sort_keys.csv', output_directory, 0.01)
    # plot_pie_chart(directory, 'sort_methods.csv', output_directory, 0.01)
    
    # deprecated
    # TODO : plot_histogram(directory, 'nest.csv', output_directory)
    # TODO : plot_histogram(directory, 'hash.csv', output_directory)
    # TODO : plot_histogram(directory, 'aggregate.csv', output_directory)

def main():
    # plot_tables('tables')
    plot_queries('queries')

if __name__ == "__main__":
    main()