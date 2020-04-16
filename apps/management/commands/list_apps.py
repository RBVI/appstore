# vim: set expandtab shiftwidth=4 softtabstop=4:

from django.core.management.base import BaseCommand

class Command(BaseCommand):

    help = "list all bundles"

    def handle(self, *args, **options):
        self.list_all_bundles()

    def list_all_bundles(self):
        from cxtoolshed3.apps.models import App
        for app in App.objects.all():
            self._list_bundle(app)

    def _list_bundle(self, app):
        print(app.name, app.fullname, "active:", app.active)
