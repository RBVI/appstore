import os, os.path
import sys

# SITE_PARENT_DIR = '/usr/local/projects/chimerax/www/preview'
# SITE_DIR = os.path.join(SITE_PARENT_DIR, 'cxtoolshed')
SITE_DIR = os.path.dirname(__file__)
SITE_PARENT_DIR = os.path.dirname(SITE_DIR)

sys.path.append(SITE_PARENT_DIR)
sys.path.append(SITE_DIR)
sys.path.append('/usr/lib/python3/dist-packages')
sys.path.append('/usr/local/lib/python3.6/dist-packages/')
li = ['/usr/local/lib/python2.7/dist-packages','/usr/lib/python2.7/dist-packages']
for i in li:
	try:
		sys.path.remove(i)
	except:
		print()
os.environ['PYTHON_EGG_CACHE'] = filejoin(SITE_DIR, '.python-egg')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django
django.setup()
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
