from django.urls import include, re_path
import apps.views
import download.views
import apps.devel

urlpatterns = [
    re_path(r'^$',				apps.views.apps_default),
    #re_path(r'^review/', include('review.urls')),
    re_path(r'^all_$',				apps.views.all_apps_downloads,             name='all_apps_downloads'),
    re_path(r'^all_new$',			apps.views.all_apps_newest,             name='all_apps_newest'),
    re_path(r'^all$',				apps.views.all_apps,             name='all_apps'),
    re_path(r'^wall$',				apps.views.wall_of_apps,         name='wall_of_apps'),
    re_path(r'^developers$',			apps.views.bundle_developers,    name='bundle_developers'),
    re_path(r'^with_tag/(\w{1,100})$',		apps.views.apps_with_tag,        name='tag_page'),
    re_path(r'^with_author/(.{1,300})$',	apps.views.apps_with_author,     name='author_page'),
    re_path(r'^(\w{1,100})$',			apps.views.app_page,             name='app_page'),
    re_path(r'^(\w{1,100})/edit$',		apps.views.app_page_edit,        name='app_page_edit'),
    re_path(r'^(\w{1,100})/author_names$',	apps.views.author_names),
    re_path(r'^(\w{1,100})/institution_names$',	apps.views.institution_names),
    re_path(r'^(\w{1,100})/download/(.{1,31})$', download.views.release_download), # old url for downloads
    re_path(r'^devel/release$',			apps.devel.release,              name='devel_release'),
    re_path(r'^devel/new_bundle$',		apps.devel.new_bundle,           name='devel_new_bundle'),
    re_path(r'^devel/new_version$',		apps.devel.new_version,          name='devel_new_version'),
    re_path(r'^devel/clean$',			apps.devel.clean,                name='devel_clean'),
]
