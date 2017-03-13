from zipfile import BadZipfile
from apps.models import App, Release, VersionRE
from django.utils.encoding import smart_unicode
from util.view_util import get_object_or_none
from util.chimerax_util import Bundle

def process_wheel(wheel_file, expect_app_name):
    try:
        bundle = Bundle(wheel_file)
    except (BadZipfile, IOError, ValueError):
        raise ValueError('is not a valid wheel file')
    app_name = smart_unicode(bundle.package, errors='replace')
    if expect_app_name and (not app_name == expect_app_name):
        raise ValueError('has app name as <tt>%s</tt> but must be <tt>%s</tt>' % (app_name, expect_app_name))
    app_ver = smart_unicode(bundle.version, errors='replace')
    # XXX: Handle "environment" key properly
    app_dependencies = []
    app_works_with = None
    for d in bundle.metadata[u'run_requires']:
        for dep in d[u'requires']:
            parts = dep.split(None, 1)
            if len(parts) == 1:
                # Version is missing, make something up for now
                name = parts[0]
                version = "(>=0.1)"
            else:
                name = parts[0]
                version = parts[1].strip()
            if name == "ChimeraX-Core" or name == "chimerax.core":
                app_works_with = version
            else:
                app_dependencies.append((name, version))
    app_works_with = smart_unicode(app_works_with, errors='replace')

    try:
        app_dependencies = list(_app_dependencies_to_releases(app_dependencies))
    except ValueError as e:
        (msg, ) = e.args
        raise ValueError('has a problem app dependencies: ' + msg)

    return (app_name, app_ver, app_works_with, app_dependencies, False)

def _app_dependencies_to_releases(app_dependencies):
    for dependency in app_dependencies:
        app_name, app_version = dependency

        app = get_object_or_none(App, active = True, fullname = app_name)
        if not app:
            raise ValueError('dependency on "%s": no such app exists' % app_name)

        release = get_object_or_none(Release, app = app, version = app_version, active = True)
        if not release:
            raise ValueError('dependency on "%s" with version "%s": no such release exists' % (app_name, app_version))

        yield release
