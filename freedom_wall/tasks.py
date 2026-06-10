from datetime import date, timedelta

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


@shared_task
def purge_old_posts():
    from freedom_wall.models import FreedomPost
    from core.utils import log_action

    today = date.today()
    cutoff = today - timedelta(days=3)
    old_posts = FreedomPost.objects.filter(created_at__date__lt=cutoff)
    count, _ = old_posts.delete()
    if count:
        log_action(
            actor=None,
            action="FREEDOM_WALL_PURGED_OLD",
            resource_type="FreedomPost",
            resource_id="all",
            metadata={"deleted_count": count, "cutoff_date": str(cutoff)},
        )
    return count
