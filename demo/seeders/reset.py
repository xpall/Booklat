"""Safe removal of demo-owned records."""

from __future__ import annotations

from django.db import transaction
from django.db.models import Q

from demo.seeders.common import demo_category_names, demo_isbns


def reset_demo_data():
    from accounts.models import User
    from announcements.models import Announcement
    from audit.models import AuditLog
    from books.models import Book, Category
    from demo.models import DemoProfile
    from freedom_wall.models import FreedomPost, FreedomPostUpvote
    from inventory.models import BookCopy, CopyHistory
    from loans.models import Loan
    from requests_app.models import CheckoutRequest

    isbns = demo_isbns()
    demo_users = User.objects.filter(demo_profile__isnull=False)
    user_ids = list(demo_users.values_list("pk", flat=True))

    counts = {
        "users": len(user_ids),
        "books": Book.objects.filter(isbn__in=isbns).count(),
        "copies": BookCopy.objects.filter(book__isbn__in=isbns).count(),
        "loans": Loan.objects.filter(
            Q(user_id__in=user_ids) | Q(book_copy__book__isbn__in=isbns)
        ).count(),
        "requests": CheckoutRequest.objects.filter(
            Q(user_id__in=user_ids) | Q(book__isbn__in=isbns)
        ).count(),
        "posts": FreedomPost.objects.filter(user_id__in=user_ids).count(),
        "announcements": Announcement.objects.filter(
            created_by_id__in=user_ids
        ).count(),
        "audit_logs": AuditLog.objects.filter(actor_id__in=user_ids).count(),
    }

    with transaction.atomic():
        FreedomPostUpvote.objects.filter(
            Q(user_id__in=user_ids) | Q(post__user_id__in=user_ids)
        ).delete()
        FreedomPost.objects.filter(user_id__in=user_ids).delete()
        Loan.objects.filter(
            Q(user_id__in=user_ids) | Q(book_copy__book__isbn__in=isbns)
        ).delete()
        CheckoutRequest.objects.filter(
            Q(user_id__in=user_ids) | Q(book__isbn__in=isbns)
        ).delete()
        CopyHistory.objects.filter(book_copy__book__isbn__in=isbns).delete()
        BookCopy.objects.filter(book__isbn__in=isbns).delete()
        Book.objects.filter(isbn__in=isbns).delete()
        Announcement.objects.filter(created_by_id__in=user_ids).delete()
        AuditLog.objects.filter(actor_id__in=user_ids).delete()
        DemoProfile.objects.filter(user_id__in=user_ids).delete()
        User.objects.filter(pk__in=user_ids).delete()

        for name in demo_category_names():
            category = Category.objects.filter(name=name).first()
            if category and not category.book_set.exists():
                category.delete()

    return counts
