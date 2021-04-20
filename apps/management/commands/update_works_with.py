# vim: set expandtab shiftwidth=4:

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = "update bundle's work_with"

    def add_arguments(self, parser):
        parser.add_argument("--replace",
                            dest="replace",
                            help="replace existing works_with value")
        parser.add_argument("--add",
                            dest="add",
                            help="add to existing works_with value")
        parser.add_argument("bundle", # nargs='?',
                            help="The bundle name")
        parser.add_argument("version", nargs='?',
                            help="The bundle version")
        parser.add_argument("platform", nargs='?',
                            help="The platform")

    def handle(self, *args, **options):
        replace = validated_spec(options["replace"])
        add = validated_spec(options["add"])
        bundle = options['bundle']
        version = options['version']
        platform = options['platform']
        if replace is None == add is None:
            print("must give one of --replace or --add")
            raise SystemExit(2)
        if bundle is None and version is None and platform is None:
            print("must give a bundle")
            raise SystemExit(2)
        elif version is None and platform is None:
            from .utils import find_bundle
            app = find_bundle(self, bundle)
            if app is None:
                print("bundle not found")
                raise SystemExit(1)
            self.update_bundle(app, replace, add)
        elif platform is None:
            from .utils import find_bundle_version
            rel = find_bundle_version(self, bundle, version, None)
            if rel is None:
                print("not find bundle with that version")
                raise SystemExit(1)
            self.update_release(rel, replace, add)
        else:
            from .utils import find_bundle_version
            rel = find_bundle_version(self, bundle, version, platform)
            if rel is None:
                print("not find bundle with that version and platform")
                raise SystemExit(1)
            self.update_release(rel, replace, add)

    def update_bundle(self, bundle, replace, add):
        from cxtoolshed3.apps.models import App
        for app in App.objects.filter(name__contains=bundle):
            self.update_all_releases(app, replace, add)

    def update_all_releases(self, app, replace, add):
        from cxtoolshed3.apps.models import Release
        for rel in Release.objects.filter(app=app):
            self.update_release(rel, replace, add)

    def update_release(self, rel, replace, add):
        # Get replace/add works_with
        if replace:
            rel.works_with = replace
        else:
            rel.works_with = rel.works_with[:-1] + ',' + add[1:]
        rel.save()
        print("Updated works_with for", rel)


def validated_spec(spec):
    if spec is None:
        return None
    from packaging.specifiers import Specifier, InvalidSpecifier
    spec = spec.strip()
    if spec.startswith('('):
        spec = spec[1:]
    if spec.endswith(')'):
        spec = spec[:-1]
    specs = spec.split(',')
    for spec in specs:
        try:
            Specifier(spec)
        except InvalidSpecifier as e:
            print(e)
            raise SystemExit(1)
    return f"({spec})"
