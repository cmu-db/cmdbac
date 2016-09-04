"""
WSGI config for CMDBAC project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys

# Change the env variable where django looks for the settings module
# http://stackoverflow.com/a/11817088
import django.conf
django.conf.ENVIRONMENT_VARIABLE = "DJANGO_CMDBAC_SETTINGS_MODULE"
os.environ.setdefault("DJANGO_CMDBAC_SETTINGS_MODULE", "cmudbac.settings")
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
