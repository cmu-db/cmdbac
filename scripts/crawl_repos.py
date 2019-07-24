#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
#sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

# setup django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

# stdlib imports
import argparse
import json
import logging ; logging.basicConfig(filename='repo_crawler.log',level=logging.DEBUG)
import time
import traceback
# django imports
from django.conf import settings
# project imports
from cmudbac.library.models import CrawlerStatus
import cmudbac.core.crawlers


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='Craws repos for information.')
    parser.add_argument('project_id', type=int)
    args = parser.parse_args()

    # reference project id
    project_id = args.project_id

    # build path to secrets
    secrets_path = os.path.join(settings.BASE_DIR, 'secrets', 'secrets.json')
    # load secrets
    try:
        with open(secrets_path, 'r') as auth_file:
            auth = json.load(auth_file)
    except:
        print( 'Failed to load secrets:', secrets_path, file=sys.stderr )
        auth = None

    while True:
        # reference data
        cs = CrawlerStatus.objects.get(id=project_id)
        repo_source = cs.source
        project_type = cs.project_type

        moduleName = 'cmudbac.core.crawlers.%s' % (repo_source.crawler_class.lower())
        module = __import__(moduleName, globals(), locals(), [repo_source.crawler_class])
        klass = getattr(module, repo_source.crawler_class)
        crawler = klass(cs, auth)

        try:
            crawler.crawl()
        except:
            traceback.print_exc()

        time.sleep(10)
        pass

    return


if __name__ == '__main__':
    main()
