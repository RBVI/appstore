# vim: set expandtab shiftwidth=4 softtabstop=4:

from optparse import make_option
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    args = "[bundle]"
    help = "delete all references to specified version of a bundle"

    def handle(self, *args, **options):
        save = self.stdout.ending
        self.stdout.ending = ''
        try:
            if len(args) == 0:
                self.list_all_releases()
            else:
                for bundle in args:
                    self.list_release(bundle)
        finally:
            self.stdout.ending = save

    def list_all_releases(self, ):
        from apps.models import App
        for app in App.objects.all():
            self._list_bundle(app)

    def list_release(self, bundle):
        from apps.models import App
        for app in App.objects.filter(name__contains=bundle):
            self._list_bundle(app)

    def _list_bundle(self, app):
        from apps.models import Release
        for rel in Release.objects.filter(app=app):
            self._list_version(app, rel)

    def _list_version(self, app, rel):
        print >> self.stdout, app.name, rel.version, "active:", rel.active
        f = rel.release_file
        print >> self.stdout, "  ", f.storage.path(f.name)
