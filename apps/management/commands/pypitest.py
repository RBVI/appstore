# vim: set expandtab shiftwidth=4 softtabstop=4:

from os import makedirs, rename
from os.path import basename, dirname, join as pathjoin, isdir, isfile
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.models import App, Tag, Release
from apps.views import _nav_panel_context
from util.view_util import html_response
from django.shortcuts import render_to_response

fields = (
  # module        model         field           filepath-func
  ('apps.models', 'App',        'icon',         'app_icon_path'),
  ('apps.models', 'Release',    'release_file', 'release_file_path'),
  ('apps.models', 'Screenshot', 'screenshot',   'screenshot_path'),
  ('apps.models', 'Screenshot', 'thumbnail',    'thumbnail_path'),
  ('apps.models', 'ReleaseAPI', 'javadocs_jar_file', 'javadocs_path'),
  ('apps.models', 'ReleaseAPI', 'pom_xml_file', 'pom_xml_path'),
)

class Command(BaseCommand):
  def handle(self, **options):
    import apps.pypi, pprint, datetime
    # pprint.pprint(apps.pypi.search({"name":["isolde"],
    #                                "description":"blast"}, "or"))
    # pprint.pprint(apps.pypi.package_roles("chimeraxisolde"))
    # pprint.pprint(apps.pypi.user_packages("Tristan Croll"))
    # pprint.pprint(apps.pypi.user_packages("tristan.croll"))
    # pprint.pprint(apps.pypi.release_downloads("chimeraxisolde", "0.9.1"))
    pprint.pprint(apps.pypi.release_urls("chimeraxisolde", "0.9.2"))
    # pprint.pprint(apps.pypi.release_data("chimeraxisolde", "0.9.1"))
    # pprint.pprint(apps.pypi.top_packages())
    # pprint.pprint(apps.pypi.top_packages(1))
    # since = datetime.datetime(2016, 11, 3)
    # pprint.pprint(apps.pypi.updated_releases(since))
    # pprint.pprint(apps.pypi.changed_packages(since))
    # classifiers = [ "Operating System :: MacOS :: MacOS X",
    #                 "Framework :: ChimeraX" ]
    # pprint.pprint(apps.pypi.browse(classifiers))
