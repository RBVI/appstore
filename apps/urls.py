from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$',                                'apps.views.apps_default'),
    #url(r'^review/', include('review.urls')),
    url(r'^all_$',                             'apps.views.all_apps_downloads',             name='all_apps_downloads'),
    url(r'^all_new$',                             'apps.views.all_apps_newest',             name='all_apps_newest'),
    url(r'^all$',                             'apps.views.all_apps',             name='all_apps'),
    url(r'^wall$',                            'apps.views.wall_of_apps',         name='wall_of_apps'),
    url(r'^developers$',                      'apps.views.bundle_developers',    name='bundle_developers'),
    url(r'^with_tag/(\w{1,100})$',            'apps.views.apps_with_tag',        name='tag_page'),
    url(r'^with_author/(.{1,300})$',          'apps.views.apps_with_author',     name='author_page'),
    url(r'^(\w{1,100})$',                     'apps.views.app_page',             name='app_page'),
    url(r'^(\w{1,100})/edit$',                'apps.views.app_page_edit',        name='app_page_edit'),
    url(r'^(\w{1,100})/author_names$',        'apps.views.author_names'),
    url(r'^(\w{1,100})/institution_names$',   'apps.views.institution_names'),
    url(r'^(\w{1,100})/download/(.{1,31})$',  'download.views.release_download'), # old url for downloads
    url(r'^devel/release$',                   'apps.devel.release',              name='devel_release'),
    url(r'^devel/new_bundle$',                'apps.devel.new_bundle',           name='devel_new_bundle'),
    url(r'^devel/new_version$',               'apps.devel.new_version',          name='devel_new_version'),
    url(r'^devel/clean$',                     'apps.devel.clean',                name='devel_clean'),
)
