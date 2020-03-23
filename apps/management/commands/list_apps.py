# vim: set expandtab shiftwidth=4 softtabstop=4:

from optparse import make_option
from django.core.management.base import BaseCommand
from .utils import fix_line_ending

class Command(BaseCommand):

    args = ""
    help = "list all bundles"

    @fix_line_ending
    def handle(self, *args, **options):
        self.list_all_bundles()

    def list_all_bundles(self):
        from apps.models import App
        for app in App.objects.all():
            self._list_bundle(app)

    def _list_bundle(self, app):
        print(app.name, app.fullname, "active:", app.active)
