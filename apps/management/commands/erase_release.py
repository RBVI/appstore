# vim: set expandtab shiftwidth=4 softtabstop=4:

from django.core.management.base import BaseCommand

class Command(BaseCommand):

    help = "delete all references to specified version of a bundle"

    def add_arguments(self, parser):
        parser.add_argument("--delete",
                            action="store_true",
                            dest="delete",
                            default=False,
                            help="really delete instead of dry run")
        parser.add_argument("bundle",
                            help="The bundle name name")
        parser.add_argument("version",
                            help="The bundle version")
        parser.add_argument("platform", nargs='?',
                            help="The platform")

    def handle(self, *args, **options):
        dry_run = not options["delete"]
        bundle = options['bundle']
        version = options['version']
        platform = options['platform']
        from .utils import find_bundle_version
        rel = find_bundle_version(self, bundle, version, platform)
        if rel is None:
            return
        from .utils import erase_release
        erase_release(self, rel, dry_run)
