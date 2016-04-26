#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: zeyuanxy
# @Date:   2016-03-21 01:52:14
# @Last Modified by:   zeyuanxy
# @Last Modified time: 2016-04-10 23:18:30
import sys
import os
import numpy as np 
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import operator as o
import seaborn as sns

FIG_DIRECTORY = os.path.join(os.path.dirname(__file__), os.pardir, 'fig')

def plot_clustered_bar_chart(ax, dpoints, ordinal = False, x_label = None, y_label = None, legend_location = 'upper left'):
    '''
    Create a barchart for data across different categories with
    multiple conditions for each category.
    
    @param ax: The plotting axes from matplotlib.
    @param dpoints: The data set as an (n, 3) numpy array
    '''
    conditions = [(c, c)
                    for c in np.unique(dpoints[:,0])]
    if ordinal:
        # Aggregate the categories according to their
        # values
        categories = [(c, float(c)) 
                      for c in np.unique(dpoints[:,1])]
    else:
        # Aggregate the categories according to their
        # mean values
        categories = [(c, np.mean(dpoints[dpoints[:,1] == c][:,2].astype(float))) 
                      for c in np.unique(dpoints[:,1])]
    
    # sort the conditions, categories and data so that the bars in
    # the plot will be ordered by category and condition
    conditions = [c[0] for c in sorted(conditions, key=o.itemgetter(1))]
    categories = [c[0] for c in sorted(categories, key=o.itemgetter(1))]
    
    dpoints = np.array(sorted(dpoints, key=lambda x: categories.index(x[1])))

    # the space between each set of bars
    space = 0.3
    n = len(conditions)
    width = (1 - space) / (len(conditions))
    
    # Create a set of bars at each position
    colors = sns.color_palette("Paired")
    for i,cond in enumerate(conditions):
        indeces = range(1, len(categories)+1)
        vals = dpoints[dpoints[:,0] == cond][:,2].astype(np.float)
        pos = [j - (1 - space) / 2. + i * width for j in indeces]
        # ax.bar(pos, vals, width=width, label=cond, color=cm.Accent(float(i) / n))
        ax.bar(pos, vals, width=width, label=cond, color=colors[i])
    
    # Set the x-axis tick labels to be equal to the categories
    ax.set_xticks(indeces)
    ax.set_xticklabels(categories)
    # plt.setp(plt.xticks()[1], rotation=90)
    
    # Add the axis labels
    ax.set_ylabel(y_label)
    ax.set_xlabel(x_label)
    
    # Add a legend
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc=legend_location)

def plot_histogram(directory, csv_file, output_directory, x_label, y_label, bin_size = None, max_value = None, ordinal = True):
    count = {}
    stats = {}
    with open(os.path.join(directory, csv_file), 'r') as f:
        description = f.readline()
        for line in f.readlines():
            cells = line.strip().split(',')
            label = cells[0]
            if label not in count:
                count[label] = 0
            if label not in stats:
                stats[label] = {}
            
            if ordinal:
                count[label] += 1
                value = int(cells[1])
                bin_index = (int(value) / bin_size) * bin_size
                if max_value != None:
                    bin_index = min(bin_index, max_value)
                if bin_index not in stats[label]:
                    stats[label][bin_index] = 0
                stats[label][bin_index] += 1
            else:
                bin_index = cells[1]
                value = int(cells[2])
                count[label] += value
                if bin_index not in stats[label]:
                    stats[label][bin_index] = 0
                stats[label][bin_index] += value

    data = []
    sub_labels = set()
    for label in stats:
        for sub_label in stats[label]:
            sub_labels.add(sub_label)
    for label in stats:
        for sub_label in sub_labels:
            data.append([label, sub_label, round(float(stats[label].get(sub_label, .0)) / count[label] * 100, 2)])
    data = np.array(data)

    plt.clf()
    fig = plt.figure()
    ax = fig.add_subplot(111)
    if ordinal:
        plot_clustered_bar_chart(ax, data, ordinal, x_label, y_label, 'upper right')
    else:
        plot_clustered_bar_chart(ax, data, ordinal, x_label, y_label)

    name = csv_file.split('.')[0]
    fig.savefig(os.path.join(output_directory, name + '.pdf'))
    plt.close(fig)

def plot_tables(directory):
    output_directory = os.path.join(FIG_DIRECTORY, 'tables')

    # active
    plot_histogram(directory, 'num_tables.csv', output_directory, '# of Tables', '% of Applications', bin_size = 10, max_value = 100)
    plot_histogram(directory, 'num_indexes.csv', output_directory, '# of Tables', '% of Applications', bin_size = 10, max_value = 100)
    plot_histogram(directory, 'num_constraints.csv', output_directory, '# of Tables', '% of Applications', bin_size = 20, max_value = 200)
    plot_histogram(directory, 'num_foreignkeys.csv', output_directory, '# of Tables', '% of Applications', bin_size = 10, max_value = 100)

    plot_histogram(directory, 'column_num.csv', output_directory, '# of Columns', '% of Tables', 1, max_value = 10)
    plot_histogram(directory, 'column_nullable.csv', output_directory, 'Nullable of Columns', '% of Columns', ordinal = False)
    plot_histogram(directory, 'column_type.csv', output_directory, 'Type of Columns', '% of Columns', ordinal = False)
    plot_histogram(directory, 'column_extra.csv', output_directory, 'Modifier of Columns', '% of Columns', ordinal = False)
    
    # working

    # deprecated

def plot_queries(directory):
    output_directory = os.path.join(FIG_DIRECTORY, 'queries')

    # active
    plot_histogram(directory, 'query_type.csv', output_directory, 'Type of Queries', '% of Queries', ordinal = False)

    plot_histogram(directory, 'table_coverage.csv', output_directory, 'Coverage of Tables', '% of Applications', bin_size = 10, max_value = 100)
    plot_histogram(directory, 'column_coverage.csv', output_directory, 'Coverage of Columns', '% of Applications', bin_size = 10, max_value = 100)
    plot_histogram(directory, 'index_coverage.csv', output_directory, 'Coverage of Indexes', '% of Applications', bin_size = 10, max_value = 100)
    plot_histogram(directory, 'table_access.csv', output_directory, '# of Tables Accessed', '% of Queries', bin_size = 1, max_value = 5)

    plot_histogram(directory, 'sort_key_count.csv', output_directory, '# of Sory Keys', '% of Sorts', ordinal = False)
    plot_histogram(directory, 'sort_key_type.csv', output_directory, 'Type of Sort Keys', '% of Sorts', ordinal = False)

    plot_histogram(directory, 'scan_type.csv', output_directory, 'Type of Scans', '% of Scans', ordinal = False)

    plot_histogram(directory, 'logical_operator.csv', output_directory, 'Logical Opeators', '% of Logical Opeators', ordinal = False)

    plot_histogram(directory, 'aggregate_operator.csv', output_directory, 'Aggregate Opeators', '% of Aggregate Opeators', ordinal = False)

    plot_histogram(directory, 'nested_count.csv', output_directory, '# of Nested Loops', '% of Nested Queries', ordinal = False)
    plot_histogram(directory, 'nested_operator.csv', output_directory, 'Type of Nested Opeators', '% of Nested Opeators', ordinal = False)

    # plot_table(directory, 'having_count.csv', output_directory)
    # plot_table(directory, 'group_count.csv', output_directory)
    
    plot_histogram(directory, 'join_type.csv', output_directory, 'Type of Joins', '% of Joins', ordinal = False)
    plot_histogram(directory, 'join_key_type.csv', output_directory, 'Type of Join Keys', '% of Join Keys', ordinal = False)
    plot_histogram(directory, 'join_key_constraint.csv', output_directory, 'Status of Join Key', '% of Join Keys', ordinal = False)
    
    # working
    
    # deprecated
   
def main():
    plot_tables('tables')
    plot_queries('queries')

if __name__ == "__main__":
    main()