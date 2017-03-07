# vim: set expandtab shiftwidth=4 softtabstop=4:

class Command(BaseCommand):
  def handle(self, **options):
    from pprint import pprint
    import apps.pypi, pprint, datetime
    # pprint(apps.pypi.search({"name":["isolde"],
    #                                "description":"blast"}, "or"))
    # pprint(apps.pypi.package_roles("chimeraxisolde"))
    # pprint(apps.pypi.user_packages("Tristan Croll"))
    # pprint(apps.pypi.user_packages("tristan.croll"))
    # pprint(apps.pypi.release_downloads("chimeraxisolde", "0.9.1"))
    pprint(apps.pypi.release_urls("chimeraxisolde", "0.9.2"))
    # pprint(apps.pypi.release_data("chimeraxisolde", "0.9.1"))
    # pprint(apps.pypi.top_packages())
    # pprint(apps.pypi.top_packages(1))
    # since = datetime.datetime(2016, 11, 3)
    # pprint(apps.pypi.updated_releases(since))
    # pprint(apps.pypi.changed_packages(since))
    # classifiers = [ "Operating System :: MacOS :: MacOS X",
    #                 "Framework :: ChimeraX" ]
    # pprint(apps.pypi.browse(classifiers))
