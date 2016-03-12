#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import re
import sqlparse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from library.models import *

def analyze_joins():
    result = {}
    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            queries = Query.objects.filter(action = action)
            for query in queries:
                content = query.content.upper()
                has_join = False
                if 'JOIN' in content:
                    parsed = sqlparse.parse(content)[0]
                    for token in parsed.tokens:
                        if token.is_keyword and 'JOIN' in token.value:
                            result[token.value] = result.get(token.value, 0) + 1
                            has_join = True
                if has_join:
                    print content
                    # TODO : do something here to judge the attributes types and statuses
                    for explain in Explain.objects.filter(query = query):
                        print explain.output
                        return

    print result

def count_repetitive_queries():
    result = {}
    for repo in Repository.objects.filter(latest_attempt__result = 'OK'):
        for action in Action.objects.filter(attempt = repo.latest_attempt):
            # TODO : count the number of repetitive queries per action (queries that are the same and will produce the exact same result)
            queries = Query.objects.filter(action = action)
            for query in queries:
                pass

def main():
    analyze_joins()

if __name__ == '__main__':
    main()
