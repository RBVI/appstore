# vim: set expandtab shiftwidth=4 softtabstop=4:

from optparse import make_option
from django.core.management.base import BaseCommand
from utils import fix_line_ending

class Command(BaseCommand):

    args = "[bundle [version]]"
    help = "extract documentation from bundle"

    @fix_line_ending
    def handle(self, *args, **options):
        if len(args) == 0:
            self.extract_all_bundles()
        elif len(args) == 1:
            bundle = args[0]
            from utils import find_bundle
            app = find_bundle(self, bundle)
            if app is None:
                return
            self.extract_bundle(app)
        elif len(args) == 2:
            bundle, version = args
            app = find_bundle(self, bundle)
            if app is None:
                return
            from utils import find_bundle_version
            rel = find_bundle_version(self, bundle, version, None)
            if rel is None:
                return
            self.extract_release(app, rel)
        else:
            from utils import print_help
            print_help(self)
            return

    def extract_all_bundles(self):
        from apps.models import App
        for app in App.objects.all():
            self.extract_newest_release(app)

    def extract_bundle(self, bundle):
        from apps.models import App
        for app in App.objects.filter(name__contains=bundle):
            self.extract_newest_release(app)

    def extract_newest_release(self, app):
        from apps.models import Release
        version = None
        release = None
        for rel in Release.objects.filter(app=app):
            ver = rel.version_tuple
            if version is None or ver > version:
                version = ver
                release = rel
        self.extract_release(app, rel)

    def extract_release(self, app, rel):
        dist = rel.distribution()
        if not dist:
            return
        bundle_name = dist["bundle_name"]
        bundle_info = dist["bundle"][bundle_name]
        version = rel.version
        package = bundle_info["app_package_name"]
        doc_path = package.replace('.', '/') + "/doc/"
        skip = len(package) + 1
        import zipfile, os.path, settings
        with zipfile.ZipFile(rel.release_file.path) as zf:
            save_dir = None
            for zi in zf.infolist():
                n = zi.filename.find(doc_path)
                if n < 0:
                    continue
                if save_dir is None:
                    save_dir = os.path.join(settings.SITE_DIR, "bundle_docs",
                                            bundle_name)
                    makedir_if_missing(save_dir)
                save_file = os.path.join(save_dir, zi.filename[n + skip:])
                parent_dir = os.path.dirname(save_file)
                makedir_if_missing(parent_dir)
                with open(save_file, "wb") as fo, zf.open(zi, "r") as fi:
                    fo.write(fi.read())


def makedir_if_missing(dirpath):
    import os.path, os
    if os.path.exists(dirpath):
        return
    parent = os.path.dirname(dirpath)
    makedir_if_missing(parent)
    os.mkdir(dirpath)
