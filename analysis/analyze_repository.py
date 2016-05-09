#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

from utils import filter_repository

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *

def repository_stats():
    stats = {}

    for project_type in ProjectType.objects.all():
        project_type_name = project_type.name
        stats[project_type_name] = []

        for repo in Repository.objects.filter(project_type = project_type).exclude(latest_successful_attempt = None):
            if filter_repository(repo):
                continue
            transaction_count = 0

            for action in Action.objects.filter(attempt = repo.latest_successful_attempt):
                transaction = ''
                for query in Query.objects.filter(action = action):
                    if 'BEGIN' in query.content.upper() or 'START TRANSACTION' in query.content.upper():
                        transaction = query.content + '\n'
                    elif transaction != '':
                        transaction += query.content + '\n'
                        if 'COMMIT' in query.content.upper():
                            transaction = transaction.strip('\n')
                        
                            # for each transaction, count the number of transactions
                            transaction_count += 1

            if transaction_count > 0:
                stats[project_type_name].append((repo.commits_count, transaction_count, repo))

    for project_type_name in stats:
        print project_type_name

        for transaction_count, commits_count, repo in sorted(stats[project_type_name], reverse = True):
            print repo.name, 'commits:{}'.format(commits_count), 'txns:{}'.format(transaction_count)
            print 'http://cmdbac.cs.cmu.edu/attempt/' + str(repo.latest_successful_attempt.id)

        print '------------------------------'
        
def main():
    # active
    repository_stats()
    
    # working
    
    # deprecated
if __name__ == '__main__':
    main()
