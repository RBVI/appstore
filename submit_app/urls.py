from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^$',                      views.submit_app,         name='submit-app'),
    re_path(r'^pending$',               views.pending_apps,       name='pending-apps'),
#    re_path(r'^cy2xplugins$',           views.cy2x_plugins,       name='cy2x-plugins'),
    re_path(r'^confirm/(\d{1,5})$',     views.confirm_submission, name='confirm-submission'),
#    re_path(r'^submit_api/(\d{1,5})$',  views.submit_api,         name='submit-api'),
#    re_path(r'^artifact_exists$',       views.artifact_exists),
]
