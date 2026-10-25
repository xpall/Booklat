"""Seed the demo user accounts."""

from __future__ import annotations

from django.conf import settings

from accounts.models import Role, User
from demo.models import DemoProfile
from demo.seeders.common import (
    DemoSeedError,
    datetime_days_ago,
    load_json,
)


def seed_users():
    roles = {role.name: role for role in Role.objects.all()}
    missing = {"Administrator", "Staff", "Member"} - set(roles)
    if missing:
        raise DemoSeedError(
            "Required roles are missing. Run `python manage.py seed_data` first."
        )

    users = {}
    for item in load_json("users.json"):
        lrn = item["lrn"]
        existing = User.objects.filter(lrn=lrn).first()
        if existing and not DemoProfile.objects.filter(user=existing).exists():
            raise DemoSeedError(
                f"User {lrn} already exists and is not a demo account. "
                "Refusing to overwrite it."
            )

        role = roles[item["role"]]
        user, created = User.objects.update_or_create(
            lrn=lrn,
            defaults={
                "first_name": item["first_name"],
                "last_name": item["last_name"],
                "role": role,
                "status": item.get("status", User.Status.ACTIVE),
                "must_change_password": False,
                "failed_login_attempts": 0,
                "locked_until": None,
            },
        )

        if created or not user.check_password(settings.DEMO_PASSWORD):
            user.set_password(settings.DEMO_PASSWORD)
            user.save(update_fields=["password"])

        DemoProfile.objects.get_or_create(user=user)

        last_login = None
        if item.get("last_login_days_ago") is not None:
            last_login = datetime_days_ago(item["last_login_days_ago"], hour=8, minute=30)

        User.objects.filter(pk=user.pk).update(
            created_at=datetime_days_ago(item.get("created_days_ago", 365), hour=8),
            last_login=last_login,
        )
        user.refresh_from_db(fields=["created_at", "last_login"])
        users[lrn] = user

    return users


def deactivate_demo_users():
    from demo.models import DemoProfile

    for profile in DemoProfile.objects.select_related("user"):
        user = profile.user
        if user.status != User.Status.SUSPENDED:
            user.status = User.Status.SUSPENDED
            user.save(update_fields=["status"])
