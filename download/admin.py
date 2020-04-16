from django.contrib import admin
from .models import *

admin.site.register(GeoLoc)
admin.site.register(ReleaseDownloadsByDate)
admin.site.register(AppDownloadsByGeoLoc)
