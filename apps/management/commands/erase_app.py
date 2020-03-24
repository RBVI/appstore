# vim: set expandtab shiftwidth=4 softtabstop=4:

from optparse import make_option, OptionError
from django.core.management.base import BaseCommand, CommandError
from .utils import fix_line_ending

class Command(BaseCommand):

    help = "delete all references to specified app"

    def add_arguments(self, parser):
        parser.add_argument("--delete",
                            action="store_true",
                            dest="delete",
                            default=False,
                            help="really delete instead of dry run")
        parser.add_argument("app_name",
                            help="The internal app name")

    @fix_line_ending
    def handle(self, *args, **options):
        dry_run = not options["delete"]
        app_name = options['app_name']
        from .utils import find_bundle
        app = find_bundle(self, app_name)
        if app is None:
            raise SystemExit(1)
        from .utils import erase_app
        erase_app(self, app, dry_run)
