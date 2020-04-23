# vim: set expandtab shiftwidth=4:

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = "list metadata associated with a bundle version"

    def add_arguments(self, parser):
        parser.add_argument("bundle", nargs='?',
                            help="The bundle name")
        parser.add_argument("version", nargs='?',
                            help="The bundle version")
        parser.add_argument("platform", nargs='?',
                            help="The platform")

    def handle(self, *args, **options):
        bundle = options['bundle']
        version = options['version']
        platform = options['platform']
        if bundle is None and version is None and platform is None:
            self.list_all_bundles()
        elif version is None and platform is None:
            from .utils import find_bundle
            app = find_bundle(self, bundle)
            if app is None:
                return
            self.list_bundle(app)
        elif platform is None:
            bundle, version = args
            from .utils import find_bundle_version
            rel = find_bundle_version(self, bundle, version, None)
            if rel is None:
                return
            self.list_release(rel)
        else:
            bundle, version, platform = args
            from .utils import find_bundle_version
            rel = find_bundle_version(self, bundle, version, platform)
            if rel is None:
                return
            self.list_release(rel)

    def list_all_bundles(self):
        from cxtoolshed3.apps.models import App
        for app in App.objects.all():
            self.list_all_releases(app)

    def list_bundle(self, bundle):
        from cxtoolshed3.apps.models import App
        for app in App.objects.filter(name__contains=bundle):
            self.list_all_releases(app)

    def list_all_releases(self, app):
        from cxtoolshed3.apps.models import Release
        for rel in Release.objects.filter(app=app):
            self.list_release(rel)

    def list_release(self, rel):
        dist = rel.distribution()
        if dist:
            import json
            print(json.dumps(dist))
        else:
            print("No metadata found")
