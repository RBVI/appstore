from zipfile import BadZipfile
from apps.models import App, Release, VersionRE
from django.utils.encoding import smart_unicode
from util.view_util import get_object_or_none
from util.chimerax_util import Bundle

def process_wheel(wheel_file, expect_app_name):
    # Make sure it is a wheel and supports a single platform
    import os.path
    filename = wheel_file.name
    root, ext = os.path.splitext(os.path.basename(filename))
    if ext != ".whl":
        raise ValueError('"%s" is not a Python wheel' % filename)
    parts = root.split('-')
    if len(parts) != 5 and len(parts) != 6:
        raise ValueError('"%s" is not a properly named Python wheel' % filename)
    # platform is the output from distutils.util.get_platform,
    # which we convert into what will be stored in our model
    # and presented to the user in web pages
    pf = parts[-1]
    if '.' in pf:
        raise ValueError('"%s" supports more than one platform' % filename)
    if pf.startswith("win_"):
        app_platform = "Windows"
    elif pf.startswith("linux_"):
        app_platform = "Linux"
    elif pf.startswith("macosx_"):
        app_platform = "macOS"
    elif pf == "any":
        app_platform = ""
    else:
        raise ValueError('"%s" targets unsupported platform' % filename)

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

    return (app_name, app_ver, app_platform, app_works_with, app_dependencies, False)

def _app_dependencies_to_releases(app_dependencies):
    for dependency in app_dependencies:
        app_name, app_version = dependency
        # pip likes '-', but we use '_'
        app_name = app_name.replace('-', '_')
        # If the dependency is not within ChimeraX, we trust
        # that it will come from pypi
        if not app_name.startswith("ChimeraX_"):
            continue
        app = get_object_or_none(App, active = True, fullname = app_name)
        if not app:
            raise ValueError('dependency on "%s": no such app exists' % app_name)
        comparison, preferred_version = _dependency_version(app_version)
        if comparison != '>=':
            raise ValueError('unsupport version operator: "%s"' % comparison)
        #release = get_object_or_none(Release, app = app, version = app_version, active = True)
        release = None
        for r in Release.objects.filter(app=app, active=True):
            rv = _version_tuple(r.version)
            if rv == preferred_version:
                release = r
                break
            elif rv > preferred_version:
                release = r
        if not release:
            raise ValueError('dependency on "%s" with version "%s": no such release exists' % (app_name, app_version))

        yield release

# Parser for version specification in bundle dependencies.
# Currently, we only support "(>= version)" where "version"
# is compatible with the toolshed version scheme.  Standard
# version numbers like "0.1.4" work fine.
import re
_DependencyVersionRE = re.compile(r'\s*\(\s*([=!<>]*)\s*(\S+)\)')

def _dependency_version(s):
    m = _DependencyVersionRE.match(s)
    if not m:
        raise ValueError("Unsupported dependency version: %r" % s)
    (comparison, version) = m.groups()
    return comparison, _version_tuple(version)

def _version_tuple(v):
    m = VersionRE.match(v)
    if not m:
        raise ValueError("Unsupported version: %r" % v)
    (major, minor, patch, tag) = m.groups()
    major = int(major) if major else 0
    minor = int(minor) if minor else 0
    patch = int(patch) if patch else 0
    tag = tag.lower() if tag else ""
    return (major, minor, patch, tag)
