import os, os.path
import sys

# SITE_PARENT_DIR = '/usr/local/projects/chimerax/www/preview'
# SITE_DIR = os.path.join(SITE_PARENT_DIR, 'cxtoolshed3')
SITE_DIR = os.path.dirname(__file__)
SITE_PARENT_DIR = os.path.dirname(SITE_DIR)

# if SITE_PARENT_DIR not in sys.path:
# 	sys.path.append(SITE_PARENT_DIR)
if SITE_DIR not in sys.path:
	sys.path.append(SITE_DIR)
os.environ['PYTHON_EGG_CACHE'] = os.path.join(SITE_DIR, '.python-egg')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django
django.setup()
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
