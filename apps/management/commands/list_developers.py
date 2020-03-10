# vim: set expandtab shiftwidth=4 softtabstop=4:

from optparse import make_option
from django.core.management.base import BaseCommand
from utils import fix_line_ending

class Command(BaseCommand):

    args = ""
    help = "list all developers"

    @fix_line_ending
    def handle(self, *args, **options):
        self.list_developers()

    def list_developers(self):
        from apps.models import App
        developers = []
        for app in App.objects.filter(active = True):
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
                email = None
                email_type = None
        print >> self.stdout, '\t'.join([app.display_name, email, email_type])
