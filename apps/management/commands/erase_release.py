# vim: set expandtab shiftwidth=4 softtabstop=4:

from optparse import make_option
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    args = "bundle version"
    help = "delete all references to specified version of a bundle"
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
            if len(args) != 2:
                from utils import print_help
                print_help(self)
                return
            dry_run = not options["delete"]
            bundle, version = args
            from utils import find_bundle_version
            rel = find_bundle_version(self, bundle, version)
            if rel is None:
                return
            from utils import erase_release
            erase_release(self, rel, dry_run)
        finally:
            self.stdout.ending = save
