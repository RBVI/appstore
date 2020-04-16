# vim: set expandtab shiftwidth=4 softtabstop=4:

from django.core.management.base import BaseCommand

class Command(BaseCommand):
  def handle(self, **options):
    from pprint import pprint
    from cxtoolshed3.apps import pypi
    import datetime
    # pprint(pypi.search({"name":["isolde"],
    #                                "description":"blast"}, "or"))
    # pprint(pypi.package_roles("chimeraxisolde"))
    # pprint(pypi.user_packages("Tristan Croll"))
    # pprint(pypi.user_packages("tristan.croll"))
    # pprint(pypi.release_downloads("chimeraxisolde", "0.9.1"))
    pprint(pypi.release_urls("chimeraxisolde", "0.9.2"))
    # pprint(pypi.release_data("chimeraxisolde", "0.9.1"))
    # pprint(pypi.top_packages())
    # pprint(pypi.top_packages(1))
    # since = datetime.datetime(2016, 11, 3)
    # pprint(pypi.updated_releases(since))
    # pprint(pypi.changed_packages(since))
    # classifiers = [ "Operating System :: MacOS :: MacOS X",
    #                 "Framework :: ChimeraX" ]
    # pprint(apps.pypi.browse(classifiers))
