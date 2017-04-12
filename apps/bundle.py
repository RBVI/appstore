# vim: set expandtab shiftwidth=4 softtabstop=4:

#
# "handler" is referenced from ../urls.py
#
from django.views.decorators.csrf import csrf_exempt
import logging

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
    try:
        name = path_parts[2]
    except IndexError:
        name = None
    try:
        version = path_parts[3]
    except IndexError:
        version = None
    response = _format_bundle(name, version)
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

def _format_bundle(name, version):
    import os.path
    from models import Release
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
    dlist = [d for d in [rel.distribution() for rel in releases]
             if d is not None]
    from django.http import HttpResponse
    import json
    response = HttpResponse(json.dumps(dlist), content_type='application/json')
    return response
