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
        if len(args) != 2:
            print_help(self)
            return

        #
        # Find the specified bundle
        #
        bundle, version = args
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
        # Find the specified version
        #
        from apps.models import Release
        rels = Release.objects.filter(app=app, version=version)
        if len(rels) == 0:
            print >> self.stderr, ("no match for bundle \"%s\" version \"%s\""
                                    % (bundle, version))
            return
        elif len(rels) > 1:
            print >> self.stderr, ("too many matches for bundle \"%s\" "
                                    "version \"%s\"" % (bundle, version))
            for rel in rels:
                print >> self.stderr, "  ", app.name, rel.version
            return
        rel = rels[0]
        dry_run = not options["delete"]
        erase_release(self, app, rel, dry_run)


def erase_release(cmd, app, rel, dry_run=True):
    """Erase all traces of app/rel from database and media storage."""

    from apps.models import Release, ReleaseAPI
    #
    # There should not be any release APIs since ChimeraX
    # does not support that yet
    #
    apis = ReleaseAPI.objects.filter(release=rel)
    if len(apis) != 0:
        print >> cmd.stderr, "cannot delete release with API"
        return

    #
    # Make sure there are no dependents on this version
    #
    deps = rel.dependencies.all()
    if len(deps) > 0:
        print >> cmd.stderr, "cannot delete release with dependencies"
        for dep in deps:
            print >> cmd.stderr, "  ", dep.app.name, dep.app.version

    #
    # Warn caller if this is the only release of this bundle
    #
    all_rels = Release.objects.all()
    if len(all_rels) == 1:
        print >> cmd.stdout, ("Warning: \"%s\" is the only release "
                                "of bundle \"%s\""
                                % (rel.version, app.name))

    #
    # XXX: Might want to get confirmation from caller here
    #
    if dry_run:
        print >> cmd.stdout, "Dry run only.  No actual deletion."
    print >> cmd.stdout, ("Delete bundle \"%s\" version \"%s\""
                            % (app.name, rel.version))

    #
    # Remove release media file
    #
    # Remove release file
    if dry_run:
        print >> cmd.stdout, "delete", rel.release_file.name
    else:
        rel.release_file.delete()

    #
    # Remove download references
    #
    from download.models import Download, ReleaseDownloadsByDate
    if dry_run:
        for d in Download.objects.filter(release=rel):
            print >> cmd.stdout, "delete Download instance", d
        for r in ReleaseDownloadsByDate.objects.filter(release=rel):
            print >> cmd.stdout, "delete ReleaseDownloadsByDate instance", r
    else:
        Download.objects.filter(release=rel).delete()
        ReleaseDownloadsByDate.objects.filter(release=rel).delete()

    #
    # TODO: delete bundle metadata
    #

    #
    # Remove this release
    #
    if dry_run:
        print >> cmd.stdout, "delete release", rel
    else:
        rel.delete()


def print_help(cmd):
    import sys, os.path
    prog = os.path.split(sys.argv[0])[-1]
    subcommand = cmd.__class__.__module__.split('.')[-1]
    cmd.print_help(prog, subcommand)
