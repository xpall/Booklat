"""Orchestration for the Booklat demo dataset."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from demo.seeders.common import assert_safe_to_seed, demo_isbns


def seed_all():
    from accounts.models import User
    from announcements.models import Announcement
    from audit.models import AuditLog
    from books.models import Book, Category
    from freedom_wall.models import FreedomPost
    from inventory.models import BookCopy
    from loans.models import Loan
    from requests_app.models import CheckoutRequest

    from demo.seeders.audit import seed_audit_logs
    from demo.seeders.catalog import seed_catalog
    from demo.seeders.circulation import seed_circulation
    from demo.seeders.content import seed_announcements, seed_freedom_posts
    from demo.seeders.people import seed_users

    assert_safe_to_seed()

    with transaction.atomic():
        users = seed_users()
        categories, books, copies = seed_catalog()
        loans, requests = seed_circulation(users, books, copies)
        announcements = seed_announcements(users)
        posts = seed_freedom_posts(users)
        audit_logs = seed_audit_logs(
            users,
            categories,
            books,
            copies,
            loans,
            requests,
            announcements,
            posts,
        )

    isbns = demo_isbns()
    demo_user_ids = list(
        User.objects.filter(demo_profile__isnull=False).values_list("pk", flat=True)
    )
    today = timezone.localdate()
    demo_loans = Loan.objects.filter(user_id__in=demo_user_ids)

    return {
        "users": User.objects.filter(pk__in=demo_user_ids).count(),
        "categories": Category.objects.count(),
        "books": Book.objects.filter(isbn__in=isbns).count(),
        "copies": BookCopy.objects.filter(book__isbn__in=isbns).count(),
        "loans": demo_loans.count(),
        "active_loans": demo_loans.filter(return_date__isnull=True).count(),
        "overdue": demo_loans.filter(
            return_date__isnull=True, due_date__lt=today
        ).count(),
        "requests": CheckoutRequest.objects.filter(user_id__in=demo_user_ids).count(),
        "pending_requests": CheckoutRequest.objects.filter(
            user_id__in=demo_user_ids,
            status=CheckoutRequest.Status.PENDING,
        ).count(),
        "posts": FreedomPost.objects.filter(user_id__in=demo_user_ids).count(),
        "approved_posts": FreedomPost.objects.filter(
            user_id__in=demo_user_ids,
            status=FreedomPost.Status.APPROVED,
        ).count(),
        "announcements": Announcement.objects.filter(
            created_by_id__in=demo_user_ids
        ).count(),
        "audit_logs": AuditLog.objects.filter(
            actor_id__in=demo_user_ids
        ).count(),
        "seeded_audit_logs": audit_logs,
    }
