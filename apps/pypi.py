# vim: set expandtab shiftwidth=4 softtabstop=4:

#
# "handler" is referenced from ../urls.py
#
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def handler(request):
    # Save server name for constructing download URLs
    global _server_url
    if not _server_url:
        _server_url = "https://" + request.META["SERVER_NAME"]
        port = request.META["SERVER_PORT"]
        if port != "443":
            _server_url += ':' + port
    #
    # If method is POST, then we assume it is an XMLRPC request.
    # Otherwise, from
    # https://setuptools.readthedocs.io/en/latest/easy_install.html#package-index-api
    # request.path_info should be one of:
    #  /pypi  - List all package version
    #  /pypi/
    #  /pypi/package  - List all versions of given package
    #  /pypi/package/
    #  /pypi/package/version - List single version of package
    #
    if request.method == "POST":
        from django.http import HttpResponse
        d = _get_dispatcher(request)
        data = request.body
        try:
            response = HttpResponse(d._marshaled_dispatch(data),
                                    content_type='text/xml')
        except Exception, e:
            logger.exception(e)
            raise
    else:
        path_parts = request.path_info.split('/')
        # 0 = empty, since path always starts with /
        # 1 = "pypi"
        # 2 = package
        # 3 = version
        try:
            package = path_parts[2]
        except IndexError:
            package = None
        try:
            version = path_parts[3]
        except IndexError:
            version = None
        response = _format_package_versions(package, version)
    return response

# =============================================================

#
# Constants
#
_ReleaseDataAttrs = [
    "name",
    "version",
    "stable_version",
    "author",
    "author_email",
    "maintainer",
    "maintainer_email",
    "home_page",
    "license",
    "summary",
    "description",
    "keywords",
    "platform",
    "download_url",
    "classifiers",
    "requires",
    "requires_dist",
    "provides",
    "provides_dist",
    "obsoletes",
    "obsoletes_dist",
    "project_url",
    "docs_url",
]

#
# Cached information
#
_dispatcher = None
_server_url = ""
_classifier_map = None

#
# Utility routines
#
def _get_dispatcher(request):
    global _dispatcher
    if _dispatcher is None:
        from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
        _dispatcher = SimpleXMLRPCDispatcher()
        for f in _implemented:
            _dispatcher.register_function(f)
        _dispatcher.register_introspection_functions()
    return _dispatcher

def _get_wheel_info(r):
    import os.path
    md = {}
    filename = os.path.basename(r.release_file_url)
    md["filename"] = filename
    root, ext = os.path.splitext(filename)  # ext should be ".whl"
    parts = root.split('-')
    md["distribution"] = parts[0]
    md["version"] = parts[1]
    if len(parts) == 6:
        md["build_tag"] = parts[2]
    md["python_tag"] = parts[-3]
    md["abi"] = parts[-2]
    md["platform"] = parts[-1]
    return md

def _get_release_info(r, attr):
    "Return a list of strings for attribute, or None if not available"
    if attr == "name":
        values = [r.app.fullname]
    elif attr == "version":
        values = [r.version]
    elif attr == "stable_version":
        values = [""]
    elif attr == "author":
        values = [a.name for a in r.app.authors.all()]
    elif attr == "author_email":
        values = [r.app.contact]
    elif attr == "maintainer":
        values = [e.username for e in r.app.editors.all()]
    elif attr == "maintainer_email":
        values = [r.app.contact]
    elif attr == "home_page":
        values = [r.app.website]
    elif attr == "license":
        values = [r.app.license_text]
    elif attr == "summary":
        values = [str(r.app.description)]
    elif attr == "description":
        values = [r.app.details]
    elif attr == "keywords":
        values = [t.fullname for t in r.app.tags.all()]
    elif attr == "platform":
        values = _get_wheel_info(r)["platform"]
    elif attr == "download_url":
        values = _release_url(_server_url, r)
    # elif attr == "classifiers":
    # elif attr == "requires":
    # elif attr == "requires_dist":
    # elif attr == "provides":
    # elif attr == "provides_dist":
    # elif attr == "obsoletes":
    # elif attr == "obsoletes_dist":
    elif attr == "project_url":
        values = [r.app.coderepo]
    elif attr == "docs_url":
        values = [r.app.tutorial]
    else:
        values = []
    if len(values) == 0:
        return None
    elif len(values) == 1:
        return values[0]
    else:
        return values

def _release_url(server_url, r):
    return server_url + r.release_download_url
    # Include hash information with URL
    #name, digest = r.hexchecksum.split(':')
    #return server_url + r.release_download_url + '#' + name + '=' + digest

def _search_matches(tvlist, vlist):
    vlist = [v.lower() for v in vlist]
    for tv in tvlist:
        for v in vlist:
            if tv.lower() in v:
                return True
    return False

def _get_classifiers():
    global _classifier_map
    if _classifier_map is None:
        from models import Release
        from django.conf import settings
        from util.chimerax_util import Bundle
        import os.path
        _classifier_map = {}
        releases = Release.objects.filter(active=True)
        for r in releases:
            full_path = os.path.join(settings.SITE_DIR, r.release_file_url)
            b = Bundle(full_path)
            value = (r.app.fullname, r.version)
            for c in b.metadata["classifiers"]:
                key = c.lower()
                try:
                    rset = _classifier_map[key]
                except KeyError:
                    rset = _classifier_map[key] = set()
                rset.add(value)
    return _classifier_map

def _format_package_versions(package, version):
    import os.path
    from models import Release
    if not package:
        releases = Release.objects.filter(active=True)
    else:
        package = ''.join([c for c in package if c not in '-_']).lower()
        if not version:
            releases = Release.objects.filter(active=True,
                                              app__name=package)
        else:
            releases = Release.objects.filter(active=True,
                                              app__name=package,
                                              version=version)
    lines = ["<html>", "<body>", "<ul>"]
    for r in releases:
        lines.append("<li>")
        filename = os.path.basename(r.release_file_url)
        url = _server_url + r.release_file_url
        lines.append("<a href=\"%s\" rel=\"download\">%s</a>" %
                     (url, filename))
        lines.append("</li>")
    lines.extend(["</ul>", "</body>", "</html>"])
    from django.http import HttpResponse
    response = HttpResponse('\n'.join(lines), content_type='text/html')
    return response

# =============================================================

#
# PyPI XML-RPC API and doc strings are from
# https://warehouse.pypa.io/api-reference/xml-rpc
#

_implemented = []

def implemented(f):
    _implemented.append(f)
    return f

@implemented
def list_packages():
    """Retrieve a list of the package names registered with the
    package index. Returns a list of name strings."""
    from models import App
    return [app.fullname for app in set(App.objects.filter(active=True))]

@implemented
def package_releases(package_name, show_hidden=False):
    """Retrieve a list of the releases registered for the given
    package_name, ordered by version.

    The show_hidden flag is now ignored. All versions are returned."""
    from models import Release
    releases = Release.objects.filter(active=True, app__fullname=package_name)
    return [r.version for r in releases]

@implemented
def package_roles(package_name):
    """Retrieve a list of [role, user] for a given package_name.
    Role is either Maintainer or Owner."""
    from models import App
    apps = App.objects.filter(fullname=package_name)
    roles = []
    for app in apps:
        for a in app.authors.all():
            roles.append(["Owner", a.name])
        for e in app.editors.all():
            roles.append(["Maintainer", e.username])
    return roles

@implemented
def user_packages(user):
    """Retrieve a list of [role, package_name] for a given user.
    Role is either Maintainer or Owner."""
    from models import App
    packages = []
    apps = App.objects.filter(authors__name=user)
    for app in apps:
        packages.append(["Owner", app.fullname])
    apps = App.objects.filter(editors__username=user)
    for app in apps:
        packages.append(["Maintainer", app.fullname])
    return packages

@implemented
def release_downloads(package_name, release_version):
    """Retrieve a list of [filename, download_count] for a given
    package_name and release_version."""
    from models import Release
    releases = Release.objects.filter(active=True,
                                      app__fullname=package_name,
                                      version=release_version)
    downloads = []
    for r in releases:
        winfo = _get_wheel_info(r)
        # XXX: This is incorrect since we are returning the
        # number of downloads per app, not per release, but
        # it is all we got
        downloads.append([winfo["filename"], r.app.downloads])
    return downloads

@implemented
def release_urls(package_name, release_version):
    """Retrieve a list of download URLs for the given release_version.
    Returns a list of dicts."""
    # See documentation for dictionary keys
    from models import Release
    from django.conf import settings
    import os, datetime, os.path
    releases = Release.objects.filter(active=True,
                                      app__fullname=package_name,
                                      version=release_version)
    urls = []
    for r in releases:
        if not r.active:
            continue
        d = {"has_sig": False, "packagetype": "bdist_wheel"}
        winfo = _get_wheel_info(r)
        d["filename"] = winfo["filename"]
        d["python_version"] = winfo["python_tag"]
        full_path = os.path.join(settings.SITE_DIR, r.release_file_url)
        sbuf = os.stat(full_path)
        d["size"] = sbuf.st_size
        d["url"] = _release_url(_server_url, r)
        d["comment_text"] = r.notes or ""
        # These are not useful but we have the information
        # TODO: Need to get MD5 digest from somewhere
        name, digest = r.hexchecksum.split(':')
        d[name] = digest
        # XXX: These are not correct but they are all we have
        d["downloads"] = r.app.downloads
        # t = r.created
        # d["upload_time"] = datetime.datetime(t.year, t.month, t.day)
        d["upload_time"] = r.created
        urls.append(d)
    return urls

@implemented
def release_data(package_name, release_version):
    """Retrieve metadata describing a specific release_version.
    Returns a dictionary."""
    # See documentation for dictionary keys
    from models import Release
    import os, datetime
    releases = Release.objects.filter(active=True,
                                      app__fullname=package_name,
                                      version=release_version)
    data = {}
    for r in releases:      # There should only be one
        if not r.active:
            continue
        for attr in _ReleaseDataAttrs:
            v = _get_release_info(r, attr)
            if not v:
                continue
            data[attr] = v
    return data

@implemented
def search(spec, operator="and"):
    """Search the package database using the indicated search spec."""
    # See URL for detailed description
    from models import Release
    releases = set(Release.objects.filter(active=True))
    or_results = set()
    for attr, values in spec.items():
        keep = set()
        for r in releases:
            vlist = _get_release_info(r, attr)
            if vlist is None:
                continue
            if isinstance(vlist, basestring):
                vlist = [vlist]
            if isinstance(values, basestring):
                values = [values]
            if _search_matches(values, vlist):
                keep.add(r)
            if operator == "and":
                releases = keep
            else:
                or_results.update(keep)
    if operator == "and":
        container = releases
    else:
        container = or_results
    results = []
    for r in container:
        results.append({"name":r.app.fullname,
                        "version":r.version,
                        "summary":str(r.app.description)})
    return results

@implemented
def browse(classifiers):
    """Retrieve a list of [name, version] of all releases classified
    with all of the given classifiers. classifiers must be a list of
    Trove classifier strings."""
    cmap = _get_classifiers()
    results = None
    for c in classifiers:
        try:
            s = cmap[c.lower()]
        except KeyError:
            print "no releases match", c.lower()
            # Nothing had this classifier, just return empty list
            return []
        else:
            print c.lower(), s
            if results is None:
                results = s
            else:
                results &= s
    if results is None:
        return []
    else:
        return list(results)

@implemented
def top_packages(number=None):
    """Retrieve the sorted list of packages ranked by number of
    downloads. Optionally limit the list to the number given."""
    from models import App
    apps = list(App.objects.filter(active=True))
    apps.sort(key=lambda app: app.downloads)
    apps.reverse()
    if number is not None:
        apps = apps[:number]
    return [app.fullname for app in apps]

@implemented
def updated_releases(since):
    """Retrieve a list of package releases made since the given
    timestamp. The releases will be listed in descending release date."""
    from models import Release
    releases = Release.objects.filter(active=True)
    keep = []
    for r in releases:
        if r.created > since:
            keep.append(r)
    keep.sort(key=lambda r: r.created)
    keep.reverse()
    return [[r.app.fullname, r.version] for r in keep]

@implemented
def changed_packages(since):
    """Retrieve a list of package names where those packages have
    been changed since the given timestamp. The packages will be
    listed in descending date of most recent change."""
    from models import Release
    releases = Release.objects.filter(active=True)
    keep = []
    for r in releases:
        if r.created > since:
            keep.append(r)
    keep.sort(key=lambda r: r.created)
    keep.reverse()
    seen = set()
    results = []
    for r in keep:
        if r.app in seen:
            continue
        results.append(r.app.fullname)
        seen.add(r.app)
    return results
