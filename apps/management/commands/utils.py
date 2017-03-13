# vim: set expandtab shiftwidth=4 softtabstop=4:

def find_bundle(cmd, bundle):
    "Find the specified bundle"
    from apps.models import App
    apps = App.objects.filter(name__contains=bundle)
    if len(apps) == 0:
        print >> cmd.stderr, "no match for bundle \"%s\"" % bundle
        return None
    elif len(apps) > 1:
        print >> cmd.stderr, "too many matches for bundle \"%s\"" % bundle
        for app in apps:
            print >> cmd.stderr, "  ", app.name
        return None
    else:
        return apps[0]


def find_bundle_version(cmd, bundle, version):
    "Find the specified version of the bundle"
    app = find_bundle(cmd, bundle)
    if app is None:
        return None
    from apps.models import Release
    rels = Release.objects.filter(app=app, version=version)
    if len(rels) == 0:
        print >> cmd.stderr, ("no match for bundle \"%s\" version \"%s\""
                                % (bundle, version))
        return None
    elif len(rels) > 1:
        print >> cmd.stderr, ("too many matches for bundle \"%s\" "
                                "version \"%s\"" % (bundle, version))
        for rel in rels:
            print >> cmd.stderr, "  ", app.name, rel.version
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
        print >> cmd.stdout, "clear authors"
        print >> cmd.stdout, "clear editor"
        print >> cmd.stdout, "clear tags"
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
            print >> cmd.stdout, "delete icon file", app.icon.name
        for sh in Screenshot.objects.filter(app=app):
            if sh.screenshot:
                print >> cmd.stdout, "delete screenshot file", sh.screenshot.name
            if sh.thumbnail:
                print >> cmd.stdout, "delete thumbnail file", sh.thumbnail.name
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
        print >> cmd.stdout, "delete bundle", app
    else:
        app.delete()


def erase_release(cmd, rel, dry_run=True):
    """Erase all traces of release from database and media storage."""

    app = rel.app
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
    if rel.release_file:
        if dry_run:
            print >> cmd.stdout, "delete file", rel.release_file.name
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
