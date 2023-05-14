# vi:set shiftwidth=4 expandtab:
import os
import sys

# SITE_PARENT_DIR = '/usr/local/projects/chimerax/www/preview'
# SITE_DIR = os.path.join(SITE_PARENT_DIR, 'cxtoolshed3')
SITE_DIR = os.path.dirname(__file__)
SITE_PARENT_DIR = os.path.dirname(SITE_DIR)
_module_name = os.path.basename(SITE_DIR)
_kind = os.path.basename(SITE_PARENT_DIR)  # preview or production
_home = os.path.expanduser("~cxtoolshed")

# use preview/production-site virtual environment's site-packages
# instead of local ones to allow them to be updated separately
_remove_dirs = [
    f'{_home}/.local/lib/python3.8/site-packages',
    '/usr/local/lib64/python3.8/site-packages',
    '/usr/local/lib/python3.8/site-packages',
]
_venv_packages = [
    f'{_home}/{_kind}-site/lib64/python3.8/site-packages',
    f'{_home}/{_kind}-site/lib/python3.8/site-packages',
]
for site_packages in _remove_dirs:
    try:
        sys.path.remove(site_packages)
    except Exception:
        pass
if _venv_packages[0] not in sys.path:
    sys.path[-2:-2] = _venv_packages

if SITE_PARENT_DIR not in sys.path:
    sys.path.append(SITE_PARENT_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = f'{_module_name}.settings'
import django
django.setup()
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
