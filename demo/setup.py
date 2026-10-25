"""Public entry points for demo-mode setup."""

from __future__ import annotations

from django.conf import settings


def create_demo_users():
    from demo.seeders.people import seed_users

    return seed_users()


def seed_demo_data():
    from demo.seeders import seed_all

    return seed_all()


def reset_demo_data():
    from demo.seeders.reset import reset_demo_data as _reset_demo_data

    return _reset_demo_data()


def deactivate_demo_users():
    from demo.seeders.people import deactivate_demo_users as _deactivate

    return _deactivate()


def demo_login_accounts():
    """Credentials shown on the login page when demo mode is enabled."""
    password = settings.DEMO_PASSWORD
    return [
        {"lrn": "admin", "password": password, "role": "Administrator"},
        {"lrn": "staff", "password": password, "role": "Staff"},
        {"lrn": "student", "password": password, "role": "Member"},
    ]
