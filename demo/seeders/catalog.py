"""Seed categories, books, and physical copies."""

from __future__ import annotations

from books.models import Book, Category
from inventory.models import BookCopy

from demo.seeders.common import (
    DemoSeedError,
    date_from_data,
    datetime_days_ago,
    datetime_on_date,
    load_json,
)


def seed_categories():
    categories = {}
    for index, item in enumerate(load_json("categories.json")):
        category, _ = Category.objects.update_or_create(
            name=item["name"],
            defaults={"is_archived": item.get("is_archived", False)},
        )
        Category.objects.filter(pk=category.pk).update(
            created_at=datetime_days_ago(900 + index, hour=8)
        )
        category.refresh_from_db(fields=["created_at"])
        categories[item["name"]] = category
    return categories


def _cover_url(item):
    if "cover_image" in item:
        return item["cover_image"]
    return f"https://covers.openlibrary.org/b/isbn/{item['isbn']}-L.jpg"


def seed_books(categories):
    books = {}
    for index, item in enumerate(load_json("books.json")):
        missing = [name for name in item.get("categories", []) if name not in categories]
        if missing:
            raise DemoSeedError(
                f"Book '{item['title']}' references unknown categories: {', '.join(missing)}"
            )

        book, _ = Book.objects.update_or_create(
            isbn=item["isbn"],
            defaults={
                "title": item["title"],
                "subtitle": item.get("subtitle", ""),
                "authors": item["authors"],
                "publisher": item.get("publisher", ""),
                "publication_year": item.get("publication_year"),
                "description": item.get("description", ""),
                "cover_image": _cover_url(item),
                "is_archived": item.get("is_archived", False),
            },
        )
        book.categories.set([categories[name] for name in item.get("categories", [])])

        arrival = item.get("arrival_days_ago")
        if arrival is None:
            arrival = 60 + (index * 11) % 720
        Book.objects.filter(pk=book.pk).update(
            created_at=datetime_days_ago(arrival, hour=10)
        )
        book.refresh_from_db(fields=["created_at"])
        books[item["title"]] = book

    return books


def seed_copies(books):
    copies = {}
    valid_statuses = dict(BookCopy.Status.choices)

    for item in load_json("books.json"):
        book = books[item["title"]]
        count = int(item.get("copies", 1))
        if count < 1:
            raise DemoSeedError(f"Book '{item['title']}' must have at least one copy.")

        statuses = item.get("copy_statuses", {})
        notes = item.get("copy_notes", {})
        acquisition_date = date_from_data(item.get("acquisition_date"))
        base_shelf = item.get("shelf", "GEN")

        for number in range(1, count + 1):
            key = f"{number:02d}"
            status = statuses.get(key, BookCopy.Status.AVAILABLE)
            if item.get("is_archived"):
                status = BookCopy.Status.ARCHIVED
            if status not in valid_statuses:
                raise DemoSeedError(
                    f"Book '{item['title']}' has invalid copy status: {status}"
                )

            copy_id = f"{book.isbn}#{number:02d}"
            copy, _ = BookCopy.objects.update_or_create(
                copy_id=copy_id,
                defaults={
                    "book": book,
                    "acquisition_date": acquisition_date,
                    "shelf_location": f"{base_shelf}-{number:02d}",
                    "notes": notes.get(key, ""),
                    "donor": item.get("donor", ""),
                    "status": status,
                    "is_archived": status == BookCopy.Status.ARCHIVED,
                },
            )
            created_at = (
                datetime_on_date(acquisition_date, hour=10)
                if acquisition_date
                else datetime_days_ago(500, hour=10)
            )
            BookCopy.objects.filter(pk=copy.pk).update(created_at=created_at)
            copy.refresh_from_db(fields=["created_at"])
            copies[copy_id] = copy

    return copies


def seed_catalog():
    categories = seed_categories()
    books = seed_books(categories)
    copies = seed_copies(books)
    return categories, books, copies
