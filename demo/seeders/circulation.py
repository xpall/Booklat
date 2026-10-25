"""Seed loans, checkout requests, and copy histories."""

from __future__ import annotations

from datetime import timedelta

from inventory.models import BookCopy, CopyHistory
from loans.models import Loan
from requests_app.models import CheckoutRequest

from demo.seeders.common import (
    DemoSeedError,
    datetime_days_ago,
    datetime_on_date,
    load_json,
    localdate_days_ago,
)


def seed_loans(users, books, copies):
    loans = {}
    active_copies = set()

    for item in load_json("loans.json"):
        user = users.get(item["user"])
        book = books.get(item["book"])
        if user is None:
            raise DemoSeedError(f"Loan references unknown user: {item['user']}")
        if book is None:
            raise DemoSeedError(f"Loan references unknown book: {item['book']}")

        copy_id = f"{book.isbn}#{int(item['copy']):02d}"
        copy = copies.get(copy_id)
        if copy is None:
            raise DemoSeedError(f"Loan references unknown copy: {copy_id}")

        checkout_date = localdate_days_ago(item["checkout_days_ago"])
        due_date = checkout_date + timedelta(days=int(item.get("loan_days", 14)))
        return_date = None
        if item.get("returned_days_ago") is not None:
            return_date = localdate_days_ago(item["returned_days_ago"])
            if return_date < checkout_date:
                raise DemoSeedError(
                    f"Loan {item['id']} was returned before it was checked out."
                )

        if return_date is None:
            if copy_id in active_copies:
                raise DemoSeedError(f"Two active loans use the same copy: {copy_id}")
            if copy.status not in (
                BookCopy.Status.AVAILABLE,
                BookCopy.Status.BORROWED,
            ):
                raise DemoSeedError(
                    f"Active loan {item['id']} uses a copy that is not available: "
                    f"{copy_id} ({copy.get_status_display()})"
                )
            active_copies.add(copy_id)

        processed_by = users.get(item.get("processed_by", "staff"))
        if processed_by is None:
            raise DemoSeedError(
                f"Loan {item['id']} references unknown staff account."
            )

        loan, _ = Loan.objects.update_or_create(
            loan_id=item["id"],
            defaults={
                "user": user,
                "book_copy": copy,
                "checkout_date": checkout_date,
                "due_date": due_date,
                "return_date": return_date,
                "processed_by": processed_by,
            },
        )
        Loan.objects.filter(pk=loan.pk).update(
            created_at=datetime_days_ago(item["checkout_days_ago"], hour=10, minute=15)
        )
        loan.refresh_from_db(fields=["created_at"])
        loans[item["id"]] = loan

    for copy_id in active_copies:
        BookCopy.objects.filter(copy_id=copy_id).update(
            status=BookCopy.Status.BORROWED,
            is_archived=False,
        )

    return loans


def seed_requests(users, books):
    requests = []
    valid_statuses = dict(CheckoutRequest.Status.choices)

    for item in load_json("requests.json"):
        user = users.get(item["user"])
        book = books.get(item["book"])
        if user is None:
            raise DemoSeedError(f"Request references unknown user: {item['user']}")
        if book is None:
            raise DemoSeedError(f"Request references unknown book: {item['book']}")
        if item["status"] not in valid_statuses:
            raise DemoSeedError(
                f"Request for '{item['book']}' has invalid status: {item['status']}"
            )

        processed_by = None
        processed_at = None
        if item.get("processed_by"):
            processed_by = users.get(item["processed_by"])
            if processed_by is None:
                raise DemoSeedError(
                    f"Request for '{item['book']}' references unknown staff account."
                )
        if item.get("processed_days_ago") is not None:
            if item["processed_days_ago"] > item["requested_days_ago"]:
                raise DemoSeedError(
                    f"Request for '{item['book']}' was processed before it was requested."
                )
            processed_at = datetime_days_ago(
                item["processed_days_ago"], hour=14, minute=30
            )

        request_obj, _ = CheckoutRequest.objects.update_or_create(
            user=user,
            book=book,
            defaults={
                "status": item["status"],
                "notes": item.get("notes", ""),
                "processed_by": processed_by,
                "processed_at": processed_at,
            },
        )
        CheckoutRequest.objects.filter(pk=request_obj.pk).update(
            requested_at=datetime_days_ago(
                item["requested_days_ago"], hour=11, minute=20
            )
        )
        request_obj.refresh_from_db(fields=["requested_at"])
        requests.append(request_obj)

    return requests


def seed_copy_history(users, copies, loans):
    admin = users["admin"]
    staff = users["staff"]
    copy_ids = [copy.pk for copy in copies.values()]
    CopyHistory.objects.filter(book_copy_id__in=copy_ids).delete()

    entries = []
    timestamps = []

    for copy in copies.values():
        if copy.acquisition_date:
            created_at = datetime_on_date(copy.acquisition_date, hour=10)
        else:
            created_at = datetime_days_ago(500, hour=10)
        entries.append(
            CopyHistory(
                book_copy=copy,
                event="Created",
                notes="Initial catalog entry.",
                actor=admin,
            )
        )
        timestamps.append(created_at)

        if copy.status == BookCopy.Status.ARCHIVED:
            entries.append(
                CopyHistory(
                    book_copy=copy,
                    event="Archived",
                    notes="Withdrawn from the active collection.",
                    actor=staff,
                )
            )
            timestamps.append(datetime_days_ago(20, hour=13))
        elif copy.status in (
            BookCopy.Status.LOST,
            BookCopy.Status.DAMAGED,
            BookCopy.Status.UNDER_REPAIR,
            BookCopy.Status.RESERVED,
        ):
            entries.append(
                CopyHistory(
                    book_copy=copy,
                    event=f"Status changed: Available → {copy.get_status_display()}",
                    notes=copy.notes,
                    actor=staff,
                )
            )
            timestamps.append(datetime_days_ago(15, hour=13))

    for loan in loans.values():
        entries.append(
            CopyHistory(
                book_copy=loan.book_copy,
                event="Borrowed",
                notes=f"Checked out by {loan.user.lrn}",
                actor=loan.processed_by,
            )
        )
        timestamps.append(datetime_on_date(loan.checkout_date, hour=10, minute=15))
        if loan.return_date:
            entries.append(
                CopyHistory(
                    book_copy=loan.book_copy,
                    event="Returned",
                    notes="Returned to circulation.",
                    actor=loan.processed_by,
                )
            )
            timestamps.append(datetime_on_date(loan.return_date, hour=15, minute=30))

    if not entries:
        return

    created = CopyHistory.objects.bulk_create(entries)
    for entry, timestamp in zip(created, timestamps):
        entry.timestamp = timestamp
    CopyHistory.objects.bulk_update(created, ["timestamp"])


def seed_circulation(users, books, copies):
    loans = seed_loans(users, books, copies)
    requests = seed_requests(users, books)
    seed_copy_history(users, copies, loans)
    return loans, requests
