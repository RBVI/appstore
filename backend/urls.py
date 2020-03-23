from django.urls import include, re_path
from . import views

urlpatterns = [
    re_path(r'^all_apps$', views.all),
]
