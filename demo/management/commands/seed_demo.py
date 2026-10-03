from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create/update or deactivate demo accounts based on DEMO_MODE."

    def handle(self, *args, **options):
        from demo.setup import create_demo_users, deactivate_demo_users

        if getattr(settings, "DEMO_MODE", False):
            create_demo_users()
            self.stdout.write(self.style.SUCCESS("Demo accounts created/updated."))
        else:
            deactivate_demo_users()
            self.stdout.write(self.style.SUCCESS("Demo accounts deactivated."))
