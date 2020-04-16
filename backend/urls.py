from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^all_apps$', views.all),
]
