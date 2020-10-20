# vim: set expandtab shiftwidth=4:

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = "update metadata associated with a bundle version"

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
            self.update_all_bundles()
        elif version is None and platform is None:
            from .utils import find_bundle
            app = find_bundle(self, bundle)
            if app is None:
                return
            self.update_bundle(app)
        elif platform is None:
            from .utils import find_bundle_version
            rel = find_bundle_version(self, bundle, version, None)
            if rel is None:
                return
            self.update_release(rel)
        else:
            from .utils import find_bundle_version
            rel = find_bundle_version(self, bundle, version, platform)
            if rel is None:
                return
            self.update_release(rel)

    def update_all_bundles(self):
        from cxtoolshed3.apps.models import App
        for app in App.objects.all():
            self.update_all_releases(app)

    def update_bundle(self, bundle):
        from cxtoolshed3.apps.models import App
        for app in App.objects.filter(name__contains=bundle):
            self.update_all_releases(app)

    def update_all_releases(self, app):
        from cxtoolshed3.apps.models import Release
        for rel in Release.objects.filter(app=app):
            self.update_release(rel)

    def update_release(self, rel):
        # Get rid of of old metadata
        from cxtoolshed3.apps.models import ReleaseMetadata
        ReleaseMetadata.objects.filter(release=rel).delete()
        from .utils import update_metadata
        update_metadata(self, rel)
