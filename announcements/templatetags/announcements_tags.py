from django import template
from announcements.models import Announcement

register = template.Library()


@register.simple_tag
def get_active_announcements():
    return Announcement.objects.filter(
        status=Announcement.Status.ACTIVE
    ).order_by("-created_at")
