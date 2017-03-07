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
        if len(args) != 1:
            from erase_release import print_help
            print_help(self)
            return

        #
        # Find the specified bundle
        #
        bundle = args[0]
        from apps.models import App
        apps = App.objects.filter(name__contains=bundle)
        if len(apps) == 0:
            print >> self.stderr, "no match for bundle \"%s\"" % bundle
            return
        elif len(apps) > 1:
            print >> self.stderr, "too many matches for bundle \"%s\"" % bundle
            for app in apps:
                print >> self.stderr, "  ", app.name
            return
        app = apps[0]

        #
        # Remove all versions
        #
        from apps.models import Release
        rels = Release.objects.filter(app=app)
        dry_run = not options["delete"]
        from erase_release import erase_release
        for rel in rels:
            erase_release(self, app, rel, dry_run)

        #
        # Clear associations
        #
        if dry_run:
            print >> self.stdout, "clear authors"
            print >> self.stdout, "clear editor"
            print >> self.stdout, "clear tags"
        else:
            app.authors.clear()
            app.editors.clear()
            app.tags.clear()
            # XXX: Should we remove associated objects that
            # have no other references?  Probably not tags,
            # but perhaps authors and editors?

        #
        # Remove icon and screenshot files
        #
        from apps.models import Screenshot
        if dry_run:
            print >> self.stdout, "delete icon", app.icon.name
            for sh in Screenshot.objects.filter(app=app):
                print >> self.stdout, "delete screenshot", sh.screenshot.name
                print >> self.stdout, "delete thumbnail", sh.thumbnail.name
        else:
            if app.icon:
                app.icon.delete()
            for sh in Screenshot.objects.filter(app=app):
                if sh.screenshot:
                    sh.screenshot.delete()
                if sh.thumbnail:
                    sh.thumbnail.delete()
                sh.delete()

        #
        # Remove download references
        #
        from download.models import AppDownloadsByGeoLoc
        if dry_run:
            for d in AppDownloadsByGeoLoc.objects.filter(app=app):
                d.delete()
        else:
            AppDownloadsByGeoLoc.objects.filter(app=app).delete()

        #
        # Remove this bundle
        #
        if dry_run:
            print >> self.stdout, "delete bundle", app
        else:
            app.delete()
