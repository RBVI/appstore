from zipfile import BadZipfile
from apps.models import App, Release, VersionRE
from django.utils.encoding import smart_text
from util.view_util import get_object_or_none
from util.chimerax_util import Bundle

import logging
logger = logging.getLogger(__name__)
# "logger" messages land in cxtoolshed.log, e.g., logger.warning(msg)
# Default logging level is WARNING for submit_apps.processwheel (see settings.py)

def process_wheel(filename, expect_app_name):
    # Make sure it is a wheel and supports a single platform
    import os.path
    root, ext = os.path.splitext(os.path.basename(filename))
    if ext != ".whl":
        raise ValueError("\"%s\" is not a Python wheel" % filename)
    parts = root.split('-')
    if len(parts) != 5 and len(parts) != 6:
        raise ValueError("\"%s\" is not a properly named Python wheel" %
                         filename)

    try:
        bundle = Bundle(filename)
    except (BadZipfile, IOError, ValueError) as e:
        raise ValueError("Not a valid wheel file: \"%s\"" % str(e))
    if bundle.platform == "Unknown":
        raise ValueError("Unsupported platform")
    app_name = smart_text(bundle.package, errors="replace")
    if expect_app_name:
        if app_name != expect_app_name:
            raise ValueError("App name given as \"%s\" but "
                             "must be \"%s\"" % (app_name, expect_app_name))
    app_dependencies = []
    app_works_with = None
    for dep in bundle.requires:
        parts = dep.split(None, 1)
        if len(parts) == 1:
            # Version is missing, make something up for now
            name = parts[0]
            version = "(~=0.1)"
        else:
            name = parts[0]
            version = parts[1].strip()
        if name == "ChimeraX-Core" or name == "chimerax.core":
            app_works_with = version
        else:
            app_dependencies.append((name, version))
    app_works_with = smart_text(app_works_with, errors="replace")

    # Add some computed attributes to bundle and return
    bundle.works_with = app_works_with
    bundle.app_dependencies = app_dependencies
    return bundle

def release_dependencies(app_dependencies):
    releases = []
    for dependency in app_dependencies:
        app_name, app_version = dependency
        # _find_release will throw exception and terminate on error
        r = _find_release(app_name, app_version)
        if r:
            releases.append(r)
    return releases

def _find_release(app_name, app_version):
    # pip likes '-', but we use '_'
    app_name = app_name.replace('-', '_')
    # If the dependency is not within ChimeraX, we trust
    # that it will come from pypi
    if not app_name.startswith("ChimeraX_"):
        return None
    app = get_object_or_none(App, active=True, fullname=app_name)
    if not app:
        raise ValueError("missing dependency \"%s\": bundle not on toolshed" %
                         _toolshed_display_name(app_name))
    comparison, preferred_version = _dependency_version(app_version)
    known_releases = {}
    for r in Release.objects.filter(app=app, active=True):
        known_releases[r.version] = r
    release = _version_match(comparison, preferred_version, known_releases)
    if not release:
        raise ValueError("missing dependency on \"%s\" with version \"%s\": "
                         "release not on toolshed" % (
                         _toolshed_display_name(app_name), app_version))
    return release

def _toolshed_display_name(app_name):
    bundle_name = app_name.replace('_', '-')
    if bundle_name.startswith("ChimeraX-"):
        return bundle_name[9:]
    else:
        return bundle_name

def sort_bundles_by_dependencies(bundles):
    # 1. Prime a cache with all the bundles we are about to install.
    # 2. Make sure no bundle is missing any dependencies.
    # 3. Build dependency tree and find roots.
    # 4. Post-order traversal of roots generates ordered bundle list.

    # Prime cache
    # release_cache:
    #   key = bundle name
    #   value = dictionary of version to release/bundle
    release_cache = {}
    for bundle in bundles:
        try:
            d = release_cache[bundle.package]
        except KeyError:
            release_cache[bundle.package] = {bundle.version:bundle}
        else:
            d[bundle.version] = bundle
        logger.debug(" prime cache: %s %s" % (bundle.package, bundle.version))

    # Verify bundles and build dependencies
    # depends_on:
    #   key = bundle instance
    #   value = set of bundle instances that need to be installed before key
    depends_on = {}
    for bundle in bundles:
        for dependency in bundle.app_dependencies:
            app_name, app_version = dependency
            app_name = app_name.replace('-', '_')
            logger.debug(" depends on: %s %s" % (app_name, app_version))
            # Look in cache first
            try:
                known_releases = release_cache[app_name]
            except KeyError:
                pass
            else:
                for v in known_releases.keys():
                    logger.debug("  known: %s" % v)
                comparison, preferred_version = _dependency_version(app_version)
                r = _version_match(comparison, preferred_version, known_releases)
                if r:
                    if isinstance(r, Bundle):
                        # One of the primed bundles
                        try:
                            depends_on[bundle].add(r)
                        except KeyError:
                            depends_on[bundle] = {r}
                    continue
            # Not in cache.  If bundle not already released,
            # _find_release will throw exception to terminate sorting
            r = _find_release(app_name, app_version)
            try:
                d = release_cache[r.app.fullname]
            except KeyError:
                release_cache[r.app.fullname] = {r.version:bundle}
            else:
                d[r.version] = bundle
            logger.debug(" augment cache: %s %s" % (r.app.fullname, r.version))

    # Generate ordered bundles
    ordered_bundles = []
    remainder = set(bundles)
    while remainder:
        ready = []
        for bundle in remainder:
            if bundle not in depends_on:
                ready.append(bundle)
        if not ready:
            # all bundles depend on some other bundles
            raise ValueError("circular bundle dependencies")
        for bundle in ready:
            ordered_bundles.append(bundle)
            remainder.remove(bundle)
            no_dependents = []
            for db, ds in depends_on.items():
                ds.discard(bundle)
                if not ds:
                    no_dependents.append(db)
            for db in no_dependents:
                del depends_on[db]
    return ordered_bundles

# Parser for version specification in bundle dependencies.
# Currently, we only support "(>= version)" where "version"
# is compatible with the toolshed version scheme.  Standard
# version numbers like "0.1.4" work fine.
import re
_DependencyVersionRE = re.compile(r'\s*\(\s*([=!<>]*)\s*(\S+)\)')
_VersionRE = re.compile(r'^(\d+)(?:\.(\d+))?(?:\.(\d+|\*))?(?:\.([\w-]+))?$')

def _dependency_version(s):
    m = _DependencyVersionRE.match(s)
    if not m:
        raise ValueError("Unsupported dependency version format: %\"%s\"" % s)
    (comparison, version) = m.groups()
    return comparison, _version_tuple(version)

def _version_tuple(v):
    m = _VersionRE.match(v)
    if not m:
        raise ValueError("Unsupported version format: \"%s\"" % v)
    (major, minor, patch, tag) = m.groups()
    major = int(major) if major else 0
    minor = int(minor) if minor else 0
    patch = patch.lower() if patch else ""
    tag = tag.lower() if tag else ""
    return (major, minor, patch, tag)

def _version_match(comparison, preferred_version, known_releases):
    if comparison not in [">=", "=="]:
        raise ValueError("unsupport version operator: \"%s\"" % comparison)
    release = None
    version = None
    for v, r in known_releases.items():
        try:
            rv = _version_tuple(v)
        except ValueError as e:
            raise ValueError("Unsupported version format: \"%s\" (\"%s\")" %
                             (v, str(r)))
        c = _version_compare(comparison, preferred_version, rv)
        if c == 0:
            release = r
            version = rv
            break
        elif c > 0:
            if version is None or _version_compare(">=", version, rv) > 0:
                release = r
                version = rv
    return release

def _version_compare(comparison, preferred, rv):
    # Assume both versions are 4-tuples.
    # First two elements of each tuple must be integers.
    # Third element of "preferred" is a string representing one of (integer, '', '*').
    # Third element of "rv" is a string representing one of (integer, '').
    # Fourth element may be one of ('', string).
    # Return value is:
    #  -1 if preferred > rv (rv does not satisfy requirement),
    #   0 for an exact match, and
    #  +1 if rv > preferred or preferred has '*' and matched rv.

    newer = 1 if comparison == ">=" else -1

    # Check element 0
    if preferred[0] > rv[0]:
        return -1
    if preferred[0] < rv[0]:
        return newer

    # Check element 1 (element 0 must be equal)
    if preferred[1] > rv[1]:
        return -1
    if preferred[1] < rv[1]:
        return newer

    # Check element 2 (element 0 and 1 must be equal)
    if preferred[2] == '*':
        return 1
    try:
        p = int(preferred[2])
    except ValueError:
        p = 0
    try:
        r = int(rv[2])
    except ValueError:
        r = 0
    if p > r:
        return -1
    if r > p:
        return newer

    # Check element 3 (element 0, 1 and 2 must be equal)
    if preferred[3] > rv[3]:
        return -1
    if preferred[3] < rv[3]:
        return newer
    return 0
