from django.urls import include, re_path
from django.conf.urls.static import static
from django.conf import settings
#from django.views.generic.simple import direct_to_template
from .apps import views, pypi, bundle

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    # Examples:
    # re_path(r'^$', 'cxtoolshed3.views.home', name='home'),
    # re_path(r'^cxtoolshed3/', include('cxtoolshed3.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    re_path(r'^admin/', admin.site.urls),
    re_path(r'',        include('social_django.urls', namespace='social')),
    re_path(r'^accounts/',	include('cxtoolshed3.users.urls')),
    re_path(r'^$',		views.apps_default, name='default-page'),
    re_path(r'^apps/',		include('cxtoolshed3.apps.urls')),
    re_path(r'^search',		include('haystack.urls')),
    re_path(r'^download/',	include('cxtoolshed3.download.urls')),
    re_path(r'^submit_app/',	include('cxtoolshed3.submit_app.urls')),
    re_path(r'^users/',		include('cxtoolshed3.users.urls')),
    re_path(r'^help/',		include('cxtoolshed3.help.urls')),
    re_path(r'^backend/',	include('cxtoolshed3.backend.urls')),
 #   re_path(r'^robots\.txt$',	direct_to_template,
  #           {'template': 'robots.txt', 'mimetype': 'text/plain'}),
    re_path(r'^pypi',		pypi.handler, name='pypi'),
    re_path(r'^bundle',		bundle.handler, name='bundle'),
]

if settings.DJANGO_STATIC_AND_MEDIA:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
