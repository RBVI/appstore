from django.contrib.auth.decorators import user_passes_test
def staff_required(login_url=None):
    return user_passes_test(lambda u: u.is_staff, login_url=login_url)

REPO_DIR = "/usr/local/projects/chimerax/builds/repo"

@staff_required()
def release(request):
    from util.view_util import html_response
    context = _get_parameters(request)
    new_bundles, new_versions, released = _get_bundles()
    context["new_bundles"] = new_bundles
    context["new_versions"] = new_versions
    context["released"] = released
    return html_response('devel_release.html', context, request)

@staff_required()
def clean(request):
    from util.view_util import html_response
    context = _get_parameters(request)
    errors, expired, current, ignored = _clean_bundles()
    context["expired"] = expired
    context["current"] = current
    context["ignored"] = ignored
    context["errors"] = errors
    return html_response('devel_clean.html', context, request)

@staff_required()
def new_bundle(request):
    import os, os.path
    from django.http import HttpResponseBadRequest
    from util.view_util import html_response
    from submit_app.processwheel import process_wheel
    from submit_app.processwheel import sort_bundles_by_dependencies
    context = _get_parameters(request)
    parameters = dict(request.POST.lists())
    filenames = parameters.get("file", [])
    for filename in filenames:
        if os.sep in filename:
            return HttpResponseBadRequest("bad file: %s" % filename)
    error_messages = []
    messages = []
    # First read in all wheels and order them by dependency
    bundles = []
    for filename in filenames:
        try:
            full_path = os.path.join(REPO_DIR, filename)
            bundle = process_wheel(full_path, None)
            bundles.append(bundle)
        except Exception as e:
            error_messages.append("%s: %s" % (filename, str(e)))
    if error_messages:
        context["error_msgs"] = error_messages
        return html_response('devel_new.html', context, request)
    try:
        bundles = sort_bundles_by_dependencies(bundles)
    except Exception as e:
        error_messages.append("error sorting bundles: %s" % str(e))
    else:
        try:
            # Then try installing them in order
            for bundle in bundles:
                try:
                    fullname = bundle.package
                    #messages.append("new_bundle: %s %s %s %s" %
                    #                (fullname, bundle.package,
                    #                 bundle.version, bundle.platform))
                    #messages.append("  works_with: %s" % str(bundle.works_with))
                    #for dep in bundle.app_dependencies:
                    #    messages.append("  dep: %s" % str(dep))
                    app, msgs = _create_app(request.user, bundle.path, fullname,
                                            bundle.version, bundle.platform,
                                            bundle.works_with,
                                            bundle.app_dependencies,
                                            bundle.release_notes)
                    messages.append("Bundle \"%s\" released" % bundle.package)
                    #if msgs:
                    #   messages.extend(msgs)
                except Exception as e:
                    error_messages.append("Exception: %s: %s" % (filename, str(e)))
        except Exception as e:
            error_messages.append("error creating new bundles: %s" % str(e))
    context["messages"] = messages
    context["error_msgs"] = error_messages
    return html_response('devel_new.html', context, request)

@staff_required()
def new_version(request):
    import os, os.path
    from django.http import HttpResponseBadRequest
    from util.view_util import html_response
    from util.id_util import fullname_to_name
    from submit_app.processwheel import process_wheel
    from submit_app.processwheel import sort_bundles_by_dependencies
    context = _get_parameters(request)
    parameters = dict(request.POST.lists())
    filenames = parameters.get("file", [])
    for filename in filenames:
        if os.sep in filename:
            return HttpResponseBadRequest("bad file: %s" % filename)
    error_messages = []
    messages = []
    # First read in all wheels and order them by dependency
    bundles = []
    for filename in filenames:
        try:
            full_path = os.path.join(REPO_DIR, filename)
            bundle = process_wheel(full_path, None)
            bundles.append(bundle)
        except Exception as e:
            error_messages.append("%s: %s" % (filename, str(e)))
    if error_messages:
        context["error_msgs"] = error_messages
        return html_response('devel_new.html', context, request)
    try:
        bundles = sort_bundles_by_dependencies(bundles)
    except Exception as e:
        error_messages.append("error sorting bundles: %s" % str(e))
    else:
        try:
            for bundle in bundles:
                try:
                    fullname = bundle.package
                    app = _find_app(fullname)
                    if app is None:
                        raise ValueError("%s: no such bundle", fullname)
                    name = fullname_to_name(fullname)
                    context["messages"]
                    msgs = _create_release(app, request.user, full_path,
                                           name, fullname, bundle.version,
                                           bundle.platform,
                                           bundle.works_with,
                                           bundle.app_dependencies,
                                           bundle.release_notes)
                    messages.append("Bundle \"%s\" updated" % bundle.package)
                    #if msgs:
                    #   messages.extend(msgs)
                except Exception as e:
                    error_messages.append("Exception: %s: %s" % (filename, str(e)))
        except Exception as e:
            error_messages.append("error creating new versions: %s" % str(e))
    context["messages"] = messages
    context["error_msgs"] = error_messages
    return html_response('devel_new.html', context, request)

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
        app_name = bundle.package
        try:
            candidates[app_name].append(bundle)
        except KeyError:
            candidates[app_name] = [bundle]
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
    app = _find_app(fullname)
    if app is None:
        app = App.objects.create(fullname=fullname, name=name)
        app.active = True
        app.editors.add(submitter)
        app.save()
    messages.append("app: %s %s" % (app.fullname, app.name))
    messages.extend(_create_release(app, submitter, full_path, name, fullname,
                                    version, platform, works_with,
                                    app_dependencies, release_notes))
    return app, messages

def _find_app(fullname):
    from apps.models import App
    try:
        return App.objects.get(fullname=fullname)
    except App.DoesNotExist:
        return None

def _create_release(app, submitter, full_path, name, fullname, version,
                    platform, works_with, app_dependencies, release_notes):
    from datetime import datetime
    import os.path
    from django.core.files import File
    from apps.models import Release
    from submit_app.processwheel import release_dependencies
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
    for dependee in release_dependencies(app_dependencies):
        messages.append("dependency: \"%s\" [%s]" % (dependee, dependee))
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
