import re
import hashlib
from shutil import rmtree
import subprocess
from os import mkdir, devnull
import os.path
from os.path import join as pathjoin
try:
    from urllib.parse import urljoin
except:
    from urlparse import urljoin
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse

class Author(models.Model):
	name        = models.CharField(max_length=255)
	institution = models.CharField(max_length=255, null=True, blank=True)

	search_schema = ('name', 'institution')
	search_key = 'id'

	def __str__(self):
		if not self.institution:
			return self.name
		else:
			return self.name + ' (' + self.institution + ')'

_TagCountCache = dict()

class Tag(models.Model):
	name     = models.CharField(max_length=255, unique=True)
	fullname = models.CharField(max_length=255)

	@property
	def count(self):
		global _TagCountCache
		if self.name in _TagCountCache:
			count = _TagCountCache[self.name]
		else:
			count = App.objects.filter(active = True, tags = self).count()
			_TagCountCache[self.name] = count
		return count

	search_schema = ('fullname', )
	search_key = 'name'

	def __str__(self):
		return self.name
	class Meta:
		ordering = ["name"]

GENERIC_ICON_URL = urljoin(settings.STATIC_URL, 'apps/img/app_icon_generic.png')

def app_icon_path(app, filename):
    return pathjoin(app.name, filename)

class App(models.Model):
    name         = models.CharField(max_length=127, unique=True)
    fullname     = models.CharField(max_length=127, unique=True)
    description  = models.CharField(max_length=255, blank=True, null=True)
    details      = models.TextField(blank=True, null=True)
    tags         = models.ManyToManyField(Tag, blank=True)

    icon         = models.ImageField(upload_to=app_icon_path, blank=True, null=True)

    authors      = models.ManyToManyField(Author, blank=True, through='OrderedAuthor')
    editors      = models.ManyToManyField(User, blank=True)

    cy_2x_plugin_download     = models.URLField(blank=True, null=True)
    cy_2x_plugin_version      = models.CharField(max_length=31, blank=True, null=True)
    cy_2x_plugin_release_date = models.DateField(blank=True, null=True)
    cy_2x_versions            = models.CharField(max_length=31, blank=True, null=True)

    latest_release_date       = models.DateField(blank=True, null=True)
    has_releases              = models.BooleanField(default=False)

    license_text    = models.URLField(blank=True, null=True)
    license_confirm = models.BooleanField(default=False)

    website      = models.URLField(blank=True, null=True)
    tutorial     = models.URLField(blank=True, null=True)
    citation     = models.CharField(max_length=31, blank=True, null=True)
    coderepo     = models.URLField(blank=True, null=True)
    contact      = models.EmailField(blank=True, null=True)

    stars        = models.PositiveIntegerField(default=0)
    votes        = models.PositiveIntegerField(default=0)
    downloads    = models.PositiveIntegerField(default=0)

    featured = models.BooleanField(default=False)
    competition_winner_dec_2012 = models.BooleanField(default=False)

    active = models.BooleanField(default=False)

    def is_editor(self, user):
        if not user:
            return False
        if user.is_staff or user.is_superuser:
            return True
        if user in self.editors.all():
            return True
        li = [usr.email for usr in self.editors.all()]
        return user.email in li
        

    def camelcase(self):
        return ' '.join([c for c in camel_case_split(self.fullname)])

    @property
    def display_name(self):
        return self.fullname.replace("ChimeraX_", "")

    @property
    def stars_percentage(self):
        return 100 * self.stars / self.votes / 5 if self.votes != 0 else 0

    @property
    def icon_url(self):
        return self.icon.url if self.icon else GENERIC_ICON_URL

    @property
    def releases(self):
        releases = list(self.release_set.filter(active=True).all())
        releases.sort(reverse=True)
        return releases

    @property
    def sorted_releases(self):
        # return releases in newest to oldest order
        releases = list(self.release_set.filter(active=True).all())
        releases.sort(reverse=True)
        return releases

    def update_has_releases(self):
        self.has_releases = (self.release_set.filter(active=True).count() > 0)
        self.save()

    @property
    def page_url(self):
        return reverse('app_page', args=[self.name])

    @property
    def ordered_authors(self):
        return (a.author for a in OrderedAuthor.objects.filter(app = self))

    search_schema = ('^fullname', 'description', 'details')
    search_key = 'name'

    def __str__(self):
        return self.name

class OrderedAuthor(models.Model):
    author       = models.ForeignKey(Author, models.CASCADE)
    app          = models.ForeignKey(App, models.CASCADE)
    author_order = models.PositiveSmallIntegerField(default = 0)

    def __unicode__(self):
        return unicode(self.author_order) + ': ' + self.app.name + ' by ' + self.author.name

    class Meta:
        ordering = ["author_order"]

VersionRE = re.compile(r'^(\d+)(?:\.(\d+))?(?:\.(\d)+)?(?:\.([\w-]+))?$')

def release_file_path(release, filename):
    return pathjoin(release.app.name, 'releases', release.version, filename)

class Release(models.Model):
    app           = models.ForeignKey(App, models.CASCADE)
    version       = models.CharField(max_length=31)
    platform      = models.CharField(max_length=15)
    works_with    = models.CharField(max_length=31)
    notes         = models.TextField(blank=True, null=True)
    created       = models.DateTimeField(auto_now_add=True)
    active        = models.BooleanField(default=True)

    release_file  = models.FileField(upload_to=release_file_path)
    hexchecksum   = models.CharField(max_length=511, blank=True, null=True)
    dependencies  = models.ManyToManyField('self', related_name='dependents', symmetrical=False)

    def __lt__(self, other):
        return (self.app, self.version_tuple, self.platform) < (other.app, other.version_tuple, other.platform)

    @property
    def version_tuple(self):
        from packaging.version import Version
        v = Version(self.version)
        if v.pre is not None:
            return v.release + v.pre
        return v.release

    @property
    def created_iso(self):
        return self.created.isoformat()

    @property
    def release_file_url(self):
        return self.release_file.url if self.release_file else None

    @property
    def release_download_url(self):
        return reverse('release_download', args=[self.app.name, self.version])

    @property
    def metadata_count(self):
        return len(self.get_metadata)

    @property
    def get_metadata(self):
        md_dict = {}
        for md in self.releasemetadata_set.all():
            md_set = md_dict.setdefault(md.type, set())
            md_set.add(md.name)
        for md_type in md_dict.keys():
            md_dict[md_type] = sorted(md_dict[md_type])
        return sorted(md_dict.items())

    def __str__(self):
        return self.app.fullname + ' ' + self.version

    def calc_checksum(self):
        cs = hashlib.sha512()
        f = self.release_file.file
        f.open('rb')
        while True:
            buf = f.read(128)
            if not buf: break
            cs.update(buf)
        f.close()
        self.hexchecksum = '%s:%s' % (cs.name, cs.hexdigest())
        self.save()

    def delete_files(self):
        self.release_file.delete()
        if self.releaseapi_set.count() > 0:
            api = self.releaseapi_set.get()
            api.delete_files()
            api.delete()

    def distribution(self):
        "Return metadata as dictionary."
        # A bunch of values must be lists
        force_list = set([("bundle", "categories"),
                          ("bundle", "requires"),
                          ("tool", "categories"),
                          ("command", "categories"),
                          ("dataformat", "nicknames"),
                          ("dataformat", "suffixes"),
                          ("dataformat", "mime_types"),
                          ("fetch", "prefixes"),
                          ("open", "keywords"),
                          ("save", "keywords")])
        d = {}
        for md in self.releasemetadata_set.all():
            try:
                type_d = d[md.type]
            except KeyError:
                type_d = d[md.type] = {}
            try:
                name_d = type_d[md.name]
            except KeyError:
                name_d = type_d[md.name] = {}
            if (md.type, md.key) not in force_list:
                name_d[md.key] = md.value
            else:
                try:
                    value_list = name_d[md.key]
                except KeyError:
                    name_d[md.key] = [md.value]
                else:
                    value_list.append(md.value)
        if not d:
            return None
        app = self.app
        d["bundle_name"] = app.fullname
        d["toolshed_name"] = app.name
        if app.description:
            d["description"] = app.description
        if app.details:
            d["details"] = app.details
        return d

    class Meta:
        ordering = ['-created']

def screenshot_path(screenshot, filename):
    return pathjoin(screenshot.app.name, 'screenshots', filename)

def thumbnail_path(screenshot, filename):
    return pathjoin(screenshot.app.name, 'thumbnails', filename)

class Screenshot(models.Model):
    app        = models.ForeignKey(App, models.CASCADE)
    screenshot = models.ImageField(upload_to=screenshot_path)
    thumbnail  = models.ImageField(upload_to=thumbnail_path)

    def __unicode__(self):
        return '%s - %d' % (self.app.fullname, self.id)

def javadocs_path(release_api, filename):
    return pathjoin(release_api.release.app.name, 'releases', release_api.release.version, filename)

def pom_xml_path(release_api, filename):
    return pathjoin(release_api.release.app.name, 'releases', release_api.release.version, filename)

def camel_case_split(str): 
    words = [[str[0]]] 
  
    for c in str[1:]: 
        if words[-1][-1].islower() and c.isupper(): 
            words.append(list(c)) 
        else: 
            words[-1].append(c) 
  
    return [''.join(word) for word in words] 

class ReleaseAPI(models.Model):
    release           = models.ForeignKey(Release, models.CASCADE)
    javadocs_jar_file = models.FileField(upload_to=javadocs_path)
    pom_xml_file      = models.FileField(upload_to=pom_xml_path)

    def __unicode__(self):
        return unicode(self.release)

    def extract_javadocs_jar(self):
        file = self.javadocs_jar_file
        dirpath = file.path + '-extracted'
        if not os.path.exists(dirpath):
            mkdir(dirpath)
        nullfile = open(devnull, 'w')
        subprocess.call(['unzip', file.path, '-d', dirpath], stdout = nullfile, stderr = nullfile)
        nullfile.close()

    def delete_files(self):
        dirpath = self.javadocs_jar_file.path + '-extracted'
        if os.path.exists(dirpath):
            rmtree(dirpath)
        self.javadocs_jar_file.delete()
        self.pom_xml_file.delete()

class ReleaseMetadata(models.Model):
    release           = models.ForeignKey(Release, models.CASCADE)
    type              = models.CharField(max_length=127)
    name              = models.CharField(max_length=127)
    key               = models.CharField(max_length=127)
    value             = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return unicode(self.release)
