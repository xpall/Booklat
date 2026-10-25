"""Shared helpers for the demo data seeders."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

from django.utils import timezone

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class DemoSeedError(Exception):
    """Raised when demo data cannot be seeded safely."""


def load_json(name):
    path = DATA_DIR / name
    if not path.exists():
        raise DemoSeedError(f"Missing demo data file: {path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def localdate_days_ago(days):
    return timezone.localdate() - timedelta(days=int(days))


def datetime_days_ago(days, hour=9, minute=0):
    day = localdate_days_ago(days)
    value = timezone.make_aware(
        datetime.combine(day, time(hour=hour, minute=minute)),
        timezone.get_current_timezone(),
    )
    now = timezone.now()
    if value > now:
        return now - timedelta(minutes=5)
    return value


def clamp_past(value):
    now = timezone.now()
    if value > now:
        return now - timedelta(minutes=5)
    return value


def datetime_on_date(value, hour=9, minute=0):
    if isinstance(value, str):
        value = date.fromisoformat(value)
    return timezone.make_aware(
        datetime.combine(value, time(hour=hour, minute=minute)),
        timezone.get_current_timezone(),
    )


def date_from_data(value):
    if not value:
        return None
    return date.fromisoformat(value)


def demo_isbns():
    return [item["isbn"] for item in load_json("books.json")]


def demo_category_names():
    return [item["name"] for item in load_json("categories.json")]


def assert_safe_to_seed():
    """Refuse to overwrite a database that already has a real catalog."""
    from books.models import Book

    isbns = demo_isbns()
    real_books = Book.objects.exclude(isbn__in=isbns)
    if real_books.exists():
        sample = ", ".join(real_books.values_list("title", flat=True)[:3])
        raise DemoSeedError(
            "This database already contains non-demo books "
            f"({sample}). Refusing to overwrite them with demo data."
        )
