from django.contrib.auth.decorators import user_passes_test
def staff_required(login_url=None):
    return user_passes_test(lambda u: u.is_staff, login_url=login_url)

ADMIN_URL = "../../admin"
REPO_DIR = "/usr/local/projects/chimerax/builds/repo"

@staff_required(login_url=ADMIN_URL)
def release(request):
    from util.view_util import html_response
    context = _get_parameters(request)
    new_bundles, new_versions, released = _get_bundles()
    context["new_bundles"] = new_bundles
    context["new_versions"] = new_versions
    context["released"] = released
    return html_response('devel_release.html', context, request)

@staff_required(login_url=ADMIN_URL)
def clean(request):
    from util.view_util import html_response
    context = _get_parameters(request)
    errors, expired, current, ignored = _clean_bundles()
    context["expired"] = expired
    context["current"] = current
    context["ignored"] = ignored
    context["errors"] = errors
    return html_response('devel_clean.html', context, request)

@staff_required(login_url=ADMIN_URL)
def new_bundle(request, name="new_bundle"):
    import os, os.path
    from django.http import HttpResponseBadRequest
    from util.view_util import html_response
    from submit_app.processwheel import process_wheel
    context = _get_parameters(request)
    filename = request.GET.get("file")
    if os.sep in filename:
        return HttpResponseBadRequest("bad file: %s" % filename)
    try:
        full_path = os.path.join(REPO_DIR, filename)
        (fullname, version, platform, works_with, app_dependencies,
         release_notes, _) = process_wheel(full_path, None)
        fullname = fullname.replace('-', '_')
        # context["messages"] = ["new_bundle: %s %s %s" %
        #                         (name, fullname, version)]
        app, msgs = _create_app(request.user, full_path, fullname,
                                version, platform, works_with,
                                app_dependencies, release_notes)
        context["messages"] = msgs
    except IOError as e:
        return HttpResponseBadRequest("%s: %s" % (filename, str(e)))
    except ValueError as e:
        context["error_msgs"] = [str(e)]
        return html_response('devel_new.html', context, request)
    return _edit_app(app, context, request)

@staff_required(login_url=ADMIN_URL)
def new_version(request):
    import os, os.path
    from django.http import HttpResponseBadRequest
    from util.view_util import html_response
    from submit_app.processwheel import process_wheel
    context = _get_parameters(request)
    filename = request.GET.get("file")
    if os.sep in filename:
        return HttpResponseBadRequest("bad file: %s" % filename)
    try:
        full_path = os.path.join(REPO_DIR, filename)
        (fullname, version, platform, works_with, app_dependencies,
         release_notes, _) = process_wheel(full_path, None)
        fullname = fullname.replace('-', '_')
        app = _find_app(fullname)
        if app is None:
            raise ValueError("%s: no such bundle", fullname)
        # context["messages"] = ["new_version: %s %s %s" %
        #                         (name, fullname, version)]
        context["messages"] = _create_release(app, request.user, full_path,
                                              name, fullname, version,
                                              platform, works_with,
                                              app_dependencies, release_notes)
    except IOError as e:
        return HttpResponseBadRequest("%s: %s" % (filename, str(e)))
    except ValueError as e:
        context["error_msgs"] = [str(e)]
        return html_response('devel_new.html', context, request)
    return _edit_app(app, context, request)

def _get_parameters(request):
    from apps.views import _cx_platform
    return {
        'cx_platform': _cx_platform(request),
        'go_back_to': 'home',
    }

def _get_bundles():
    import os
    from apps.models import App
    from util.chimerax_util import Bundle
    bundles = [Bundle(os.path.join(REPO_DIR, filename))
               for filename in os.listdir(REPO_DIR)
               if filename.endswith(".whl")]
    # Group bundles by package name and assign default release state
    candidates = {}
    for bundle in bundles:
        bundle_name = bundle.package.replace('-', '_')
        try:
            candidates[bundle_name].append(bundle)
        except KeyError:
            candidates[bundle_name] = [bundle]
        bundle.release_state = "new_bundle"
        bundle.app = None
    # Update bundle release state if app is known
    for app in App.objects.all():
        try:
            app_bundles = candidates[app.fullname]
        except KeyError:
            continue
        for bundle in app_bundles:
            bundle.app = app
            for release in app.releases:
                if release.version == bundle.version:
                    bundle.release_state = "released"
                    break
            else:
                bundle.release_state = "new_version"
    new_bundles = []
    new_versions = []
    released = []
    for bundle in bundles:
        if bundle.release_state == "new_bundle":
            new_bundles.append(bundle)
        elif bundle.release_state == "new_version":
            new_versions.append(bundle)
        else:
            released.append(bundle)
    if new_bundles:
        new_bundles.sort(key=lambda b: (b.package, b.version))
    if new_versions:
        new_versions.sort(key=lambda b: (b.package, b.version))
    if released:
        released.sort(key=lambda b: b.package)
    return new_bundles, new_versions, released

def _clean_bundles():
    import os
    from datetime import datetime, timedelta
    import traceback
    current = 0
    expired = 0
    ignored = 0
    errors = []
    threshold = datetime.now() - timedelta(weeks=1)
    for filename in os.listdir(REPO_DIR):
        if not filename.endswith(".whl"):
            ignored += 1
            continue
        full_path = os.path.join(REPO_DIR, filename)
        mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
        if mtime >= threshold:
            current += 1
        else:
            expired += 1
            try:
                os.remove(full_path)
            except Exception as e:
                errors.append(str(e))
    return errors, expired, current, ignored

def _create_app(submitter, full_path, fullname, version, platform,
                works_with, app_dependencies, release_notes):
    import os.path
    from apps.models import App
    from util.id_util import fullname_to_name
    messages = ["%s = %s %s" % (full_path, fullname, version)]
    # Create app (see _pending_app_accept in submit_app/views.py)
    name = fullname_to_name(fullname)
    app = App.objects.create(fullname=fullname, name=name)
    app.active = True
    app.editors.add(submitter)
    app.save()
    messages.append("app: %s %s" % (fullname, name))
    messages.extend(_create_release(app, submitter, full_path, name, fullname,
                                    version, platform, works_with,
                                    app_dependencies, release_notes))
    return app, messages

def _find_app(fullname):
    from apps.models import App
    return App.objects.filter(fullname=fullname)

def _create_release(app, submitter, full_path, name, fullname, version,
                    platform, works_with, app_dependencies, release_notes):
    from datetime import datetime
    import os.path
    from django.core.files import File
    from apps.models import Release
    messages = []
    # Create release (see _make_release in submit_app/models.py)
    release, _ = Release.objects.get_or_create(app=app, version=version,
                                               platform=platform)
    release.works_with = works_with
    release.active = True
    release.created = datetime.today()
    release.platform = platform
    if release_notes:
        release.notes = release_notes
    release.save()
    messages.append("release: %s %s" % (version, platform))
    with open(full_path, "rb") as f:
        release.release_file.save(os.path.basename(full_path), File(f))
    for dependee in app_dependencies:
        messages.append("dependency: %r [%s]" % (dependee, dependee))
        release.dependencies.add(dependee)
    release.calc_checksum()
    # Make release part of app
    if not app.has_releases:
        app.has_releases = True
    app.latest_release_date = release.created
    app.save()
    return messages

def _edit_app(app, context, request):
    from models import Tag
    from views import _AppPageEditConfig as config
    from util.view_util import html_response
    all_tags = [tag.fullname for tag in Tag.objects.all()]
    context.update({
        'app': app,
        'all_tags': all_tags,
        'max_file_img_size_b': config.max_img_size_b,
        'max_icon_dim_px': config.max_icon_dim_px,
        'thumbnail_height_px': config.thumbnail_height_px,
        'app_description_maxlength': config.app_description_maxlength,
        'release_uploaded': True,
    })
    return html_response('app_page_edit.html', context, request)
