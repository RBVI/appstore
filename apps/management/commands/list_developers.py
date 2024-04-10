# vim: set expandtab shiftwidth=4:

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = "list all developers"

    def handle(self, *args, **options):
        self.list_developers()

    def list_developers(self):
        from cxtoolshed3.apps.models import App
        for app in App.objects.filter(active=True):
            self.list_developer(app)

    def list_developer(self, app):
        if app.contact:
            email = app.contact
            email_type = "Contact"
        else:
            for editor in app.editors.all():
                if editor.email:
                    email = editor.email
                    email_type = "Editor"
                    break
            else:
                email = "MISSING"
                email_type = "MISSING"
        print('\t'.join([app.display_name, email, email_type]))
