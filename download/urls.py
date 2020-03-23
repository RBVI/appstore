from django.urls import include, re_path
import download.views

urlpatterns = [
	re_path(r'^stats/$',                                      download.views.all_stats,                   name='all_stats'),
	re_path(r'^stats/timeline$',                              download.views.all_stats_timeline),
	re_path(r'^stats/geography/all$',                         download.views.all_stats_geography_all),
	re_path(r'^stats/geography/world$',                       download.views.all_stats_geography_world),
	re_path(r'^stats/geography/country/(\w{2})$',             download.views.all_stats_geography_country),
	re_path(r'^stats/(\w{1,100})/$',                          download.views.app_stats,                   name='app_stats'),
	re_path(r'^stats/(\w{1,100})/timeline$',                  download.views.app_stats_timeline),
	re_path(r'^stats/(\w{1,100})/geography/all$',             download.views.app_stats_geography_all),
	re_path(r'^stats/(\w{1,100})/geography/world$',           download.views.app_stats_geography_world),
	re_path(r'^stats/(\w{1,100})/geography/country/(\w{2})$', download.views.app_stats_country),
 
	re_path(r'^(\w{1,100})/(.{1,31})/(\d{1,10})$',            download.views.release_download,            name='release_download'),
]
