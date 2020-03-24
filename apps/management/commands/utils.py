# vim: set expandtab shiftwidth=4 softtabstop=4:
import sys

def fix_line_ending(f):
    return f  ## TODO
    from functools import wraps
    @wraps(f)
    def wrapped_f(self, *args, **kw):
        try:
            save = self.stdout.ending
            self.stdout.ending = ''
        except AttributeError:
            pass
        rv = f(self, *args, **kw)
        try:
            self.stdout.ending = save
        except NameError:
            pass
        return rv
    return wrapped_f

def find_bundle(cmd, bundle):
    "Find the specified bundle"
    from apps.models import App
    apps = App.objects.filter(name__contains=bundle)
    if len(apps) == 0:
        print("no match for bundle \"%s\"" % bundle, file=sys.stderr)
        return None
    elif len(apps) > 1:
        for app in apps:
            if app.name == bundle:
                return app
        print(cmd.stderr, "too many matches for bundle \"%s\"" % bundle, file=sys.stderr)
        for app in apps:
            print("  ", app.name, file=sys.stderr)
        return None
    else:
        return apps[0]


def find_bundle_version(cmd, bundle, version, platform):
    "Find the specified version of the bundle"
    app = find_bundle(cmd, bundle)
    if app is None:
        return None
    from apps.models import Release
    if platform:
        rels = Release.objects.filter(app=app, version=version, platform=platform)
    else:
        rels = Release.objects.filter(app=app, version=version)
    if len(rels) == 0:
        print("no match for bundle \"%s\" version \"%s\"" % (bundle, version),
              file=sys.stderr)
        return None
    elif len(rels) > 1:
        print("too many matches for bundle \"%s\" " "version \"%s\"" % (bundle, version),
              file=sys.stderr)
        for rel in rels:
            print("  ", app.name, rel.version, file=sys.stderr)
        return None
    else:
        return rels[0]


def find_release_by_id(cmd, release_id):
    "Find the specified version of the bundle"
    from apps.models import Release
    rels = Release.objects.filter(id=release_id)
    if len(rels) == 0:
        print("no match for release id \"%s\"" % release_id, file=sys.stderr)
        return None
    elif len(rels) > 1:
        print("too many matches for release id \"%s\" " % release_id,
              file=sys.stderr)
        for rel in rels:
            print("  ", app.name, rel.version, file=sys.stderr)
        return None
    else:
        return rels[0]


def erase_app(cmd, app, dry_run):
    """Erase all traces of app from database and media storage."""
    #
    # Remove all versions (including non-active ones, which
    # is why we do not use "app.releases")
    #
    from apps.models import Release
    rels = Release.objects.filter(app=app)
    for rel in app.releases:
        erase_release(cmd, rel, dry_run)

    #
    # Clear associations
    #
    if dry_run:
        print("clear authors")
        print("clear editor")
        print("clear tags")
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
        if app.icon:
            print("delete icon file", app.icon.name)
        for sh in Screenshot.objects.filter(app=app):
            if sh.screenshot:
                print("delete screenshot file", sh.screenshot.name)
            if sh.thumbnail:
                print("delete thumbnail file", sh.thumbnail.name)
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
        print("delete bundle", app)
    else:
        app.delete()


def erase_release(cmd, rel, dry_run=True):
    """Erase all traces of release from database and media storage."""

    app = rel.app
    from apps.models import Release, ReleaseAPI

    #
    # Make sure there are no dependents on this version
    #
    #deps = rel.dependencies.all()
    deps = Release.objects.filter(dependencies__app__name=app.name).filter(dependencies__version=rel.version)
    if len(deps) > 0:
        print("cannot delete release with dependencies", file=sys.stderr)
        for dep in deps:
            print("  ", dep.app.name, dep.version, file=sys.stderr)
        return

    #
    # Warn caller if this is the only release of this bundle
    #
    all_rels = Release.objects.all()
    if len(all_rels) == 1:
        print("Warning: \"%s\" is the only release of bundle \"%s\"" % (rel.version, app.name),
              file=sys.stderr)

    #
    # XXX: Might want to get confirmation from caller here
    #
    if dry_run:
        print("Dry run only.  No actual deletion.")
    print("Delete bundle \"%s\" version \"%s\""
                            % (app.name, rel.version))

    #
    # Remove release media file
    #
    # Remove release file
    if rel.release_file:
        if dry_run:
            print("delete file", rel.release_file.name)
        else:
            rel.delete_files()

    #
    # Remove download references
    #
    from download.models import Download, ReleaseDownloadsByDate
    if dry_run:
        for d in Download.objects.filter(release=rel):
            print("delete Download instance", d)
        for r in ReleaseDownloadsByDate.objects.filter(release=rel):
            print("delete ReleaseDownloadsByDate instance", r)
    else:
        Download.objects.filter(release=rel).delete()
        ReleaseDownloadsByDate.objects.filter(release=rel).delete()

    #
    # Delete release metadata
    #
    from apps.models import ReleaseMetadata
    ReleaseMetadata.objects.filter(release=rel).delete()

    #
    # Remove this release
    #
    if dry_run:
        print("delete release", rel)
    else:
        rel.delete()


def update_metadata(cmd, rel):
    "Update metdata for a release from its wheel"
    rf = rel.release_file
    if not rf:
        print("No file associated with release", rel, file=sys.stderr)
        return
    path = rf.storage.path(rf.name)
    if not path.endswith(".whl"):
        print("Release file is not a wheel", rf, file=sys.stderr)
        return
    from util.chimerax_util import Bundle
    try:
        b = Bundle(path)
    except IOError:
        print("Release file is missing", path, file=sys.stderr)
        return
    from apps.models import ReleaseMetadata
    # XXX: Copied from submit_app/models.py
    # Get version from bundle data
    md, _ = ReleaseMetadata.objects.get_or_create(
                release=rel, type="bundle",
                name=b.package, key="version", value=b.version)
    md.save()
    try:
        for req in b.requires:
            for r in req["requires"]:
                md, _ = ReleaseMetadata.objects.get_or_create(
                            release=rel, type="bundle",
                            name=b.package, key="requires", value=r)
                md.save()
    except KeyError:
        pass
    # Get rest of metadata from bundle classifiers
    for info_type, metadata in b.info().items():
        # info_type: "bundle", "command", etc.
        for name, values in metadata.items():
            # name: "apbs", "debug ccd", etc.
            for key, value in values.items():
                # key: "synopsis", "categories ccd", etc.
                # value: either a string or a list
                if isinstance(value, str):
                    md, _ = ReleaseMetadata.objects.get_or_create(
                                release=rel, type=info_type,
                                name=name, key=key, value=value)
                    md.save()
                else:
                    for v in value:
                        md, _ = ReleaseMetadata.objects.get_or_create(
                                    release=rel, type=info_type,
                                    name=name, key=key, value=v)
                        md.save()
    print("Updated metadata for", rel)

def print_help(cmd):
    import sys, os.path
    prog = os.path.split(sys.argv[0])[-1]
    subcommand = cmd.__class__.__module__.split('.')[-1]
    cmd.print_help(prog, subcommand)
