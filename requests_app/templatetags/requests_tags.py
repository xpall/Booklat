from django import template
from requests_app.models import CheckoutRequest

register = template.Library()


@register.simple_tag
def requests_pending_count():
    return CheckoutRequest.objects.filter(
        status=CheckoutRequest.Status.PENDING,
    ).count()
