from django import template
from django.utils import timezone
from loans.models import Loan

register = template.Library()


@register.simple_tag
def loans_overdue_count():
    return Loan.objects.filter(
        return_date__isnull=True,
        due_date__lt=timezone.localdate(),
    ).count()
