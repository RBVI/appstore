# vim: set expandtab shiftwidth=4:

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = "delete all references to specified (by id) release of a bundle"

    def add_arguments(self, parser):
        parser.add_argument("--delete",
                            action="store_true",
                            dest="delete",
                            default=False,
                            help="really delete instead of dry run")
        parser.add_argument("release_id",
                            help="The release identifier")

    def handle(self, *args, **options):
        dry_run = not options["delete"]
        release_id = options["release_id"]
        from .utils import find_release_by_id
        rel = find_release_by_id(self, release_id)
        if rel is None:
            return
        from .utils import erase_release
        erase_release(self, rel, dry_run)
