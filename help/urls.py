from django.urls import include, re_path
from . import views

urlpatterns = [
    re_path(r'^about$',                     views.about,      name='about'),
    re_path(r'^contact$',                   views.contact,    name='contact'),
    re_path(r'^competitions$',              views.competitions,name='competitions'),
    re_path(r'^md$',                        views.md,         name='md'),
    re_path(r'^getstarted$',                views.getstarted, name='getstarted'),
    re_path(r'^getstarted_app_install$',    views.getstarted_app_install, name='getstarted_app_install'),
]
