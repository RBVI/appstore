# vim: set expandtab shiftwidth=4 softtabstop=4:

from optparse import make_option, OptionError
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

    args = "bundle"
    help = "delete all references to specified bundle"
    option_list = BaseCommand.option_list + (
                    make_option("--delete",
                                action="store_true",
                                dest="delete",
                                default=False,
                                help="really delete instead of dry run"),)

    def handle(self, *args, **options):
        save = self.stdout.ending
        self.stdout.ending = ''
        try:
            if len(args) != 1:
                from utils import print_help
                print_help(self)
                return
            dry_run = not options["delete"]
            bundle = args[0]
            from utils import find_bundle
            app = find_bundle(self, bundle)
            if app is None:
                return
            from utils import erase_app
            erase_app(self, app, dry_run)
        finally:
            self.stdout.ending = save
