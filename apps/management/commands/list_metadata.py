# vim: set expandtab shiftwidth=4 softtabstop=4:

from optparse import make_option
from django.core.management.base import BaseCommand
from .utils import fix_line_ending

class Command(BaseCommand):

    args = "[bundle [version [platform]]]"
    help = "list metadata associated with a bundle version"

    @fix_line_ending
    def handle(self, *args, **options):
        if len(args) == 0:
            self.list_all_bundles()
        elif len(args) == 1:
            bundle = args[0]
            from .utils import find_bundle
            app = find_bundle(self, bundle)
            if app is None:
                return
            self.list_bundle(app)
        elif len(args) == 2:
            bundle, version = args
            from .utils import find_bundle_version
            rel = find_bundle_version(self, bundle, version, None)
            if rel is None:
                return
            self.list_release(rel)
        elif len(args) == 3:
            bundle, version, platform = args
            from .utils import find_bundle_version
            rel = find_bundle_version(self, bundle, version, platform)
            if rel is None:
                return
            self.list_release(rel)
        else:
            from .utils import print_help
            print_help(self)
            return

    def list_all_bundles(self):
        from apps.models import App
        for app in App.objects.all():
            self.list_all_releases(app)

    def list_bundle(self, bundle):
        from apps.models import App
        for app in App.objects.filter(name__contains=bundle):
            self.list_all_releases(app)

    def list_all_releases(self, app):
        from apps.models import Release
        for rel in Release.objects.filter(app=app):
            self.list_release(rel)

    def list_release(self, rel):
        dist = rel.distribution()
        if dist:
            import json
            print(json.dumps(dist))
