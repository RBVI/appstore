from django.db.models import Model, CharField, PositiveIntegerField, ForeignKey, DateField, SET_NULL, CASCADE, UniqueConstraint
from ..apps.models import App, Release
from ..util.view_util import ipaddr_long_to_str

class Download(Model):
    release = ForeignKey(Release, CASCADE, related_name='app_download_stats')
    when    = DateField()
    ip4addr = PositiveIntegerField()

    def __unicode__(self):
        return unicode(self.release) + u' ' + unicode(self.when) + u' ' + ipaddr_long_to_str(self.ip4addr)

class ReleaseDownloadsByDate(Model):
    release = ForeignKey(Release, SET_NULL, null=True) # null release has total count across a given day
    when    = DateField()
    count   = PositiveIntegerField(default=0)

    class Meta:
        # avoid race condition in get_or_create(ReleaseDownloadsByDate, ...)
        # unique_together = ['release', 'when']
        constraints = [
            UniqueConstraint(fields=['release', 'when'], name='unique_by_date')
        ]

    def __unicode__(self):
        return unicode(self.release) + u' ' + unicode(self.when) + u': ' + unicode(self.count)

class GeoLoc(Model):
    country = CharField(max_length=2) # when region & city are empty, country contains the total
    region  = CharField(max_length=2,  blank=True)
    city    = CharField(max_length=63, blank=True)

    def __unicode__(self):
        return self.country + u' ' + self.region + u' ' + self.city

class AppDownloadsByGeoLoc(Model):
    app    = ForeignKey(App, SET_NULL, null=True) # null app has total count across a given geoloc
    geoloc = ForeignKey(GeoLoc, CASCADE)
    count  = PositiveIntegerField(default = 0)

    class Meta:
        # avoid race condition in get_or_create(AppDownloadsByGeoLoc, ...)
        #unique_together = ['app', 'geoloc']
        constraints = [
            UniqueConstraint(fields=['app', 'geoloc'], name='unique_by_geoloc')
        ]

    def __unicode__(self):
        return unicode(self.app) + u' ' + unicode(self.geoloc) + u': ' + unicode(self.count)
