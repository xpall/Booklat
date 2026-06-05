from celery import shared_task
from django.db import transaction


@shared_task
def purge_all_posts():
    from freedom_wall.models import FreedomPost
    from core.utils import log_action

    count, _ = FreedomPost.objects.all().delete()
    log_action(
        actor=None,
        action="FREEDOM_WALL_PURGED",
        resource_type="FreedomPost",
        resource_id="all",
        metadata={"deleted_count": count},
    )
    return count
