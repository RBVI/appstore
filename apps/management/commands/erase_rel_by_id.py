# vim: set expandtab shiftwidth=4 softtabstop=4:

from optparse import make_option
from django.core.management.base import BaseCommand
from utils import fix_line_ending

class Command(BaseCommand):

    args = "release_id"
    help = "delete all references to specified (by id) release of a bundle"
    option_list = BaseCommand.option_list + (
                    make_option("--delete",
                                action="store_true",
                                dest="delete",
                                default=False,
                                help="really delete instead of dry run"),)

    @fix_line_ending
    def handle(self, *args, **options):
        if len(args) != 1:
            from utils import print_help
            print_help(self)
            return
        dry_run = not options["delete"]
        release_id = args[0]
        from utils import find_release_by_id
        rel = find_release_by_id(self, release_id)
        if rel is None:
            return
        from utils import erase_release
        erase_release(self, rel, dry_run)
