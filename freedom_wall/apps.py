import sys

from django.apps import AppConfig


class FreedomWallConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "freedom_wall"

    def ready(self):
        if not _is_web_process():
            return
        from freedom_wall.tasks import purge_old_posts

        purge_old_posts()


def _is_web_process():
    argv = sys.argv
    if len(argv) > 1 and argv[1] == "runserver":
        return True
    if "gunicorn" in argv[0]:
        return True
    return False
