from django.urls import include, re_path
import submit_app.views

urlpatterns = [
    re_path(r'^$',                      submit_app.views.submit_app,         name='submit-app'),
    re_path(r'^pending$',               submit_app.views.pending_apps,       name='pending-apps'),
#    re_path(r'^cy2xplugins$',           submit_app.views.cy2x_plugins,       name='cy2x-plugins'),
    re_path(r'^confirm/(\d{1,5})$',     submit_app.views.confirm_submission, name='confirm-submission'),
#    re_path(r'^submit_api/(\d{1,5})$',  submit_app.views.submit_api,         name='submit-api'),
#    re_path(r'^artifact_exists$',       submit_app.views.artifact_exists),
]
