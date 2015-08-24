#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_webcrawler.settings")
import django
django.setup()

from crawler.models import *
from deployers import *
from utils import *

def main():
	if len(sys.argv) != 3:
		return
	repo_name = sys.argv[1]
	database_name = sys.argv[2]

	repo = Repository.objects.get(name=repo_name)
	database = Database.objects.get(name=database_name)
	
	moduleName = "deployers.%s" % (repo.project_type.deployer_class.lower())
	moduleHandle = __import__(moduleName, globals(), locals(), [repo.project_type.deployer_class])
	klass = getattr(moduleHandle, repo.project_type.deployer_class)
	deployer = klass(repo, database)
	if deployer.deploy() != 0:
		sys.exit(-1)

if __name__ == "__main__":
	main()