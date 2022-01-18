# vim: set expandtab shiftwidth=4:

#
# "handler" is referenced from ../urls.py
#
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os.path
from ..util.chimerax_util import Version, compatible_with, chimerax_user_agent

# import logging
# logger = logging.getLogger(__name__)
# "logger" messages should show in cxtoolshed.log.  See settings.py

DbName = os.path.join(settings.SITE_DIR, "request_logs.db")


@csrf_exempt
def handler(request):
    #
    # request.path_info should be one of:
    #  /bundle  - List all package version
    #  /bundle/
    #  /bundle/package  - List all versions of given package
    #  /bundle/package/
    #  /bundle/package/version - List single version of package
    # Returned data is in json format and consists of
    # a list of dictionaries, with each dictionary
    # representing metadata for one release of a bundle.
    #
    path_parts = request.path_info.split('/')
    # indices are:
    #   0 = empty, since path always starts with /
    #   1 = "bundle"
    #   2 = bundle_name
    #   3 = version
    cx_version, platform = chimerax_user_agent(request)
    try:
        name = path_parts[2]
    except IndexError:
        name = None
    try:
        version = path_parts[3]
    except IndexError:
        version = None
    # Additional information in query parameters or POST data
    if request.method == "POST":
        uuid = request.POST.get("uuid")
        format_version = request.POST.get("format_version")
    else:
        uuid = request.GET.get("uuid")
        format_version = request.GET.get("format_version")
    if uuid:
        log_uuid(uuid)
    try:
        format_version = int(format_version)
    except (TypeError, ValueError):
        format_version = 1
    response = _format_bundle(name, version, cx_version, platform, format_version)
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
# Utility routines
#

def _format_bundle(name, version, cx_version, platform, format_version):
    from .models import Release
    if not name:
        releases = Release.objects.filter(active=True)
    else:
        name = ''.join([c for c in name if c not in '-_']).lower()
        if not version:
            releases = Release.objects.filter(active=True,
                                              app__name__contains=name)
        else:
            releases = Release.objects.filter(active=True,
                                              app__name__contains=name,
                                              version=version)
    if platform is not None:
        releases = releases.filter(active=True, platform=platform) | releases.filter(active=True, platform="")
    if cx_version is not None:
        cx_version = Version(cx_version)
        releases = [rel for rel in releases if compatible_with(cx_version, rel.works_with)]
    dlist = [d for d in [rel.distribution(format_version) for rel in releases]
             if d is not None]
    if format_version >= 2:
        dlist.insert(0, ['format_version', format_version])
    from django.http import HttpResponse
    import json
    response = HttpResponse(json.dumps(dlist), content_type='application/json')
    return response


def log_uuid(uuid):
    """Log UUID and return row identifier."""
    import sqlite3
    from datetime import datetime
    with sqlite3.connect(DbName) as db:
        _check_table(db, "Request", SQL_CreateTable_Request)
        c = db.cursor()
        c.execute(SQL_Insert_Request, (uuid, datetime.now()))
        return c.lastrowid


def _check_table(db, table_name, create_script):
    c = db.cursor()
    c.execute(SQL_CheckTable, (table_name,))
    if not c.fetchall():
        c.executescript(create_script)


#
# SQL statements
#
SQL_Insert_Request = "INSERT INTO Request(uuid, time) VALUES (?, ?)"

#
# All tables should have a primary key "id" that autoincrements
#
SQL_CheckTable = "SELECT * FROM sqlite_master WHERE name=? AND type='table';"
SQL_CreateTable_Request = """
CREATE TABLE Request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT,
    time DATETIME
);
"""
