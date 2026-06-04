from django import template
from freedom_wall.models import FreedomPost

register = template.Library()


@register.simple_tag
def freedom_wall_pending_count():
    return FreedomPost.objects.filter(status=FreedomPost.Status.PENDING).count()
