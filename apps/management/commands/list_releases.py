# vim: set expandtab shiftwidth=4 softtabstop=4:

from django.core.management.base import BaseCommand

class Command(BaseCommand):

    help = "list all releases of a bundle"

    def add_arguments(self, parser):
        parser.add_argument("bundle", nargs='?',
                            help="The bundle name")

    def handle(self, *args, **options):
        bundle = options['bundle']
        if bundle is None:
            self.list_all_releases()
        else:
            for bundle in args:
                self.list_release(bundle)

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
        print(app.name, rel.version, "active:", rel.active)
        f = rel.release_file
        print("  ", f.storage.path(f.name))
