# vim: set expandtab shiftwidth=4 softtabstop=4:

from optparse import make_option
from django.core.management.base import BaseCommand
from utils import fix_line_ending

class Command(BaseCommand):

    args = "[bundle [version [platform]]]"
    help = "update metadata associated with a bundle version"

    @fix_line_ending
    def handle(self, *args, **options):
        if len(args) == 0:
            self.update_all_bundles()
        elif len(args) == 1:
            bundle = args[0]
            from utils import find_bundle
            app = find_bundle(self, bundle)
            if app is None:
                return
            self.update_bundle(app)
        elif len(args) == 2:
            bundle, version = args
            from utils import find_bundle_version
            rel = find_bundle_version(self, bundle, version, None)
            if rel is None:
                return
            self.update_release(rel)
        elif len(args) == 3:
            bundle, version, platform = args
            from utils import find_bundle_version
            rel = find_bundle_version(self, bundle, version, platform)
            if rel is None:
                return
            self.update_release(rel)
        else:
            from utils import print_help
            print_help(self)
            return

    def update_all_bundles(self):
        from apps.models import App
        for app in App.objects.all():
            self.update_all_releases(app)

    def update_bundle(self, bundle):
        from apps.models import App
        for app in App.objects.filter(name__contains=bundle):
            self.update_all_releases(app)

    def update_all_releases(self, app):
        from apps.models import Release
        for rel in Release.objects.filter(app=app):
            self.update_release(rel)

    def update_release(self, rel):
        # Get rid of of old metadata
        from apps.models import ReleaseMetadata
        ReleaseMetadata.objects.filter(release=rel).delete()
        from utils import update_metadata
        update_metadata(self, rel)
