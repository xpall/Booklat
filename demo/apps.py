import sys

from django.apps import AppConfig
from django.conf import settings


class DemoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "demo"

    def ready(self):
        if not _is_web_process():
            return
        demo_enabled = getattr(settings, "DEMO_MODE", False)
        from demo.setup import create_demo_users, deactivate_demo_users

        if demo_enabled:
            create_demo_users()
        else:
            deactivate_demo_users()


def _is_web_process():
    argv = sys.argv
    if len(argv) > 1 and argv[1] == "runserver":
        return True
    if "gunicorn" in argv[0]:
        return True
    return False
