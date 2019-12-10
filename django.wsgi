import os, os.path
import sys

# SITE_PARENT_DIR = '/usr/local/projects/chimerax/www/preview'
# SITE_DIR = os.path.join(SITE_PARENT_DIR, 'cxtoolshed')
SITE_DIR = os.path.dirname(__file__)
SITE_PARENT_DIR = os.path.dirname(SITE_DIR)

sys.path.append(SITE_PARENT_DIR)
sys.path.append(SITE_DIR)

os.environ['PYTHON_EGG_CACHE'] = os.path.join(SITE_DIR, '.python-egg')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
