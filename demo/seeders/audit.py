"""Generate a realistic audit trail for the demo dataset."""

from __future__ import annotations

from datetime import timedelta

from audit.models import AuditLog
from inventory.models import BookCopy

from demo.seeders.common import clamp_past, datetime_days_ago, datetime_on_date


def seed_audit_logs(
    users,
    categories,
    books,
    copies,
    loans,
    requests,
    announcements,
    posts,
):
    admin = users["admin"]
    staff = users["staff"]
    AuditLog.objects.filter(actor__in=list(users.values())).delete()

    entries = []

    def add(actor, action, resource_type, resource_id, timestamp, metadata=None):
        entries.append(
            (
                AuditLog(
                    actor=actor,
                    action=action,
                    resource_type=resource_type,
                    resource_id=str(resource_id),
                    metadata=metadata or {},
                ),
                clamp_past(timestamp),
            )
        )

    # Users
    for user in users.values():
        add(
            admin,
            "USER_CREATED",
            "User",
            user.lrn,
            user.created_at,
            {
                "role": user.role.name if user.role else "",
                "status": user.get_status_display(),
            },
        )

    suspended = [u for u in users.values() if u.status == "suspended"]
    archived = [u for u in users.values() if u.status == "archived"]
    for user in suspended:
        add(
            admin,
            "USER_SUSPENDED",
            "User",
            user.lrn,
            datetime_days_ago(20, hour=11),
            {"reason": "Repeated overdue notices."},
        )
    for user in archived:
        add(
            admin,
            "USER_ARCHIVED",
            "User",
            user.lrn,
            datetime_days_ago(40, hour=11),
            {"reason": "Account closed after transfer."},
        )
    for user in list(users.values())[3:6]:
        add(
            admin,
            "USER_UPDATED",
            "User",
            user.lrn,
            user.created_at + timedelta(days=30),
            {"field": "status"},
        )
    add(
        admin,
        "PASSWORD_RESET",
        "User",
        "202600000002",
        datetime_days_ago(15, hour=13),
        {"reason": "Member requested a password reset."},
    )

    # Categories
    for category in categories.values():
        add(
            admin,
            "CATEGORY_CREATED",
            "Category",
            category.slug,
            category.created_at,
            {"name": category.name},
        )
    first_category = next(iter(categories.values()))
    add(
        admin,
        "CATEGORY_UPDATED",
        "Category",
        first_category.slug,
        datetime_days_ago(60, hour=9),
        {"name": first_category.name},
    )

    # Books
    for index, book in enumerate(books.values()):
        actor = admin if index % 2 == 0 else staff
        add(
            actor,
            "BOOK_CREATED",
            "Book",
            book.isbn,
            book.created_at,
            {"title": book.title, "isbn": book.isbn},
        )
    for book in list(books.values())[5:8]:
        add(
            admin,
            "BOOK_UPDATED",
            "Book",
            book.isbn,
            book.created_at + timedelta(days=45),
            {"field": "description"},
        )
    for book in books.values():
        if book.is_archived:
            add(
                admin,
                "BOOK_ARCHIVED",
                "Book",
                book.isbn,
                datetime_days_ago(30, hour=14),
                {"title": book.title},
            )

    # A representative sample of copy creation logs.
    for index, copy in enumerate(copies.values()):
        if index % 4 != 0:
            continue
        add(
            staff,
            "COPY_CREATED",
            "BookCopy",
            copy.copy_id,
            copy.created_at,
            {"title": copy.book.title, "shelf": copy.shelf_location},
        )

    for copy in copies.values():
        if copy.status == BookCopy.Status.ARCHIVED:
            add(
                staff,
                "COPY_ARCHIVED",
                "BookCopy",
                copy.copy_id,
                datetime_days_ago(20, hour=13),
                {"title": copy.book.title},
            )
        elif copy.status in (
            BookCopy.Status.LOST,
            BookCopy.Status.DAMAGED,
            BookCopy.Status.UNDER_REPAIR,
            BookCopy.Status.RESERVED,
        ):
            add(
                staff,
                "COPY_STATUS_CHANGED",
                "BookCopy",
                copy.copy_id,
                datetime_days_ago(15, hour=13),
                {
                    "old_status": "Available",
                    "new_status": copy.get_status_display(),
                    "notes": copy.notes,
                },
            )

    # Loans
    for loan in loans.values():
        add(
            loan.processed_by,
            "LOAN_CREATED",
            "Loan",
            loan.loan_id,
            loan.created_at,
            {
                "user_lrn": loan.user.lrn,
                "copy_id": loan.book_copy.copy_id,
                "due_date": str(loan.due_date),
            },
        )
        if loan.return_date:
            add(
                loan.processed_by,
                "LOAN_RETURNED",
                "Loan",
                loan.loan_id,
                datetime_on_date(loan.return_date, hour=15, minute=30),
                {
                    "user_lrn": loan.user.lrn,
                    "copy_id": loan.book_copy.copy_id,
                },
            )

    # Checkout requests
    for request_obj in requests:
        add(
            request_obj.user,
            "CHECKOUT_REQUEST_CREATED",
            "CheckoutRequest",
            request_obj.pk,
            request_obj.requested_at,
            {
                "user_lrn": request_obj.user.lrn,
                "book_isbn": request_obj.book.isbn,
            },
        )
        if request_obj.status == "approved":
            add(
                request_obj.processed_by,
                "CHECKOUT_REQUEST_APPROVED",
                "CheckoutRequest",
                request_obj.pk,
                request_obj.processed_at,
                {
                    "user_lrn": request_obj.user.lrn,
                    "notes": request_obj.notes,
                },
            )
        elif request_obj.status == "fulfilled":
            add(
                request_obj.processed_by,
                "CHECKOUT_REQUEST_APPROVED",
                "CheckoutRequest",
                request_obj.pk,
                request_obj.processed_at,
                {
                    "user_lrn": request_obj.user.lrn,
                    "notes": request_obj.notes,
                },
            )
        elif request_obj.status == "rejected":
            add(
                request_obj.processed_by,
                "CHECKOUT_REQUEST_REJECTED",
                "CheckoutRequest",
                request_obj.pk,
                request_obj.processed_at,
                {
                    "user_lrn": request_obj.user.lrn,
                    "notes": request_obj.notes,
                },
            )
        elif request_obj.status == "cancelled":
            add(
                request_obj.user,
                "CHECKOUT_REQUEST_CANCELLED",
                "CheckoutRequest",
                request_obj.pk,
                request_obj.requested_at + timedelta(hours=6),
                {"user_lrn": request_obj.user.lrn},
            )

    # Freedom Wall
    for post in posts:
        add(
            post.user,
            "FREEDOM_POST_CREATED",
            "FreedomPost",
            post.pk,
            post.created_at,
            {"user_lrn": post.user.lrn, "pen_name": post.pen_name},
        )
        if post.status == "approved":
            add(
                post.processed_by,
                "FREEDOM_POST_APPROVED",
                "FreedomPost",
                post.pk,
                post.processed_at,
                {"author_lrn": post.user.lrn},
            )
        elif post.status == "rejected":
            add(
                post.processed_by,
                "FREEDOM_POST_REJECTED",
                "FreedomPost",
                post.pk,
                post.processed_at,
                {
                    "author_lrn": post.user.lrn,
                    "reason": post.rejection_reason,
                },
            )
        elif post.status == "deleted":
            add(
                post.processed_by,
                "FREEDOM_POST_DELETED",
                "FreedomPost",
                post.pk,
                post.processed_at,
                {"author_lrn": post.user.lrn},
            )

    # Announcements
    for index, announcement in enumerate(announcements):
        add(
            announcement.created_by,
            "ANNOUNCEMENT_CREATED",
            "Announcement",
            announcement.pk,
            announcement.created_at,
            {"title": announcement.title},
        )
        if announcement.status == "archived":
            add(
                announcement.created_by,
                "ANNOUNCEMENT_ARCHIVED",
                "Announcement",
                announcement.pk,
                announcement.updated_at,
                {"title": announcement.title},
            )
        elif index == 0:
            add(
                announcement.created_by,
                "ANNOUNCEMENT_UPDATED",
                "Announcement",
                announcement.pk,
                announcement.updated_at,
                {"title": announcement.title},
            )

    if not entries:
        return 0

    created = AuditLog.objects.bulk_create([entry[0] for entry in entries])
    for log, (_, timestamp) in zip(created, entries):
        log.timestamp = timestamp
    AuditLog.objects.bulk_update(created, ["timestamp"])
    return len(created)
