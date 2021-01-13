#
# vi: set shiftwidth=4 expandtab:
from zipfile import BadZipfile
from ..apps.models import App, Release
from django.utils.encoding import smart_str
from ..util.view_util import get_object_or_none
from ..util.chimerax_util import Bundle
from packaging.version import Version
from packaging.requirements import Requirement, InvalidRequirement

import logging
logger = logging.getLogger(__name__)
# "logger" messages land in cxtoolshed.log, e.g., logger.warning(msg)
# Default logging level is WARNING for submit_apps.processwheel (see settings.py)


def process_wheel(filename, expect_app_name):
    # Make sure it is a wheel and supports a single platform
    try:
        bundle = Bundle(filename)
    except (BadZipfile, IOError, ValueError) as e:
        raise ValueError("Not a valid wheel file: \"%s\"" % str(e))
    if bundle.platform == "Unknown":
        raise ValueError("Unsupported platform")
    app_name = smart_str(bundle.package, errors="replace")
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
    app_works_with = smart_str(app_works_with, errors="replace")

    # Add some computed attributes to bundle and return
    bundle.works_with = app_works_with
    bundle.app_dependencies = app_dependencies
    return bundle


def release_dependencies(app_dependencies):
    releases = []
    missing = []
    for dependency in app_dependencies:
        app_name, app_version = dependency
        # _find_release will throw exception and terminate on error
        try:
            r = _find_release(app_name, app_version)
            releases.append(r)
        except Exception:
            missing.append(f"{app_name} {app_version}")
    return releases, missing


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
    requirement = _dependency_requirement(app_name, app_version)
    known_releases = {}
    for r in Release.objects.filter(app=app, active=True):
        known_releases[r.version] = r
    release = _version_match(requirement, known_releases, app_name)
    if not release:
        raise ValueError(
            "missing dependency on \"%s\" with version \"%s\": "
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
    # (Used by apps/devel.py)
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
            release_cache[bundle.package] = {bundle.version: bundle}
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
                requirement = _dependency_requirement(app_name, app_version)
                r = _version_match(requirement, known_releases, app_name)
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
                release_cache[r.app.fullname] = {r.version: bundle}
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


def _dependency_requirement(name, specifiers):
    try:
        req = Requirement(f"{name}{specifiers}")
    except InvalidRequirement as err:
        raise ValueError(f"Invalid dependency for {name}: {err}")
    return req


def _version_match(requirement: Requirement, known_releases: {str: Release}, name: str):
    release = None
    version = None
    for v, r in known_releases.items():
        try:
            rv = Version(v)
        except ValueError:
            raise ValueError("Unsupported version format: \"%s\" (\"%s\") for name" %
                             (v, str(r), name))
        if rv in requirement.specifier:
            if release is None or rv > version:
                release = r
                version = rv
    return release


def _version_satisfies(requirement: Requirement, rv: Version):
    for s in requirement.specifiers:
        if rv not in s:
            return False
    return True
