from django.urls import include, re_path
from . import views

urlpatterns = [
    # re_path(r'', include('social_django.urls', namespace='social')),
    re_path(r'login/$',				views.login,		name='login'),
    re_path(r'^login$',				views.login,		name='login'),
    re_path(r'^login/done/([\w-]{1,100})/$',	views.login_done,	name='login_done'),
    re_path(r'^logout$',			views.logout,		name='logout'),
]
