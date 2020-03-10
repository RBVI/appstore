# vim: set expandtab shiftwidth=4 softtabstop=4:

from optparse import make_option
from django.core.management.base import BaseCommand
from utils import fix_line_ending

class Command(BaseCommand):

    args = "bundle version [platform]"
    help = "delete all references to specified version of a bundle"
    option_list = BaseCommand.option_list + (
                    make_option("--delete",
                                action="store_true",
                                dest="delete",
                                default=False,
                                help="really delete instead of dry run"),)

    @fix_line_ending
    def handle(self, *args, **options):
        if len(args) != 2 and len(args) != 3:
            from utils import print_help
            print_help(self)
            return
        dry_run = not options["delete"]
        bundle = args[0]
        version = args[1]
        platform = args[2] if len(args) == 3 else None
        from utils import find_bundle_version
        rel = find_bundle_version(self, bundle, version, platform)
        if rel is None:
            return
        from utils import erase_release
        erase_release(self, rel, dry_run)
