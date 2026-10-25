from django.conf import settings
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create/update demo content when DEMO_MODE=1, or deactivate demo accounts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete demo-owned records and rebuild the demo dataset.",
        )

    def handle(self, *args, **options):
        from demo.setup import (
            deactivate_demo_users,
            reset_demo_data,
            seed_demo_data,
        )
        from demo.seeders.common import DemoSeedError, assert_safe_to_seed

        if not settings.DEMO_MODE:
            if options["reset"]:
                raise CommandError(
                    "--reset requires DEMO_MODE=1. Refusing to delete demo content."
                )
            deactivate_demo_users()
            self.stdout.write(self.style.SUCCESS("Demo accounts deactivated."))
            return

        try:
            password_validation.validate_password(settings.DEMO_PASSWORD)
        except ValidationError as exc:
            raise CommandError(
                "DEMO_PASSWORD does not meet the password policy: "
                + " ".join(exc.messages)
            ) from exc

        try:
            assert_safe_to_seed()
            if options["reset"]:
                removed = reset_demo_data()
                self.stdout.write(
                    self.style.WARNING(
                        "Removed demo data: "
                        f"{removed['users']} users, {removed['books']} books, "
                        f"{removed['copies']} copies, {removed['loans']} loans, "
                        f"{removed['requests']} requests, {removed['posts']} posts, "
                        f"{removed['announcements']} announcements, "
                        f"{removed['audit_logs']} audit logs."
                    )
                )
            summary = seed_demo_data()
        except DemoSeedError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data ready: "
                f"{summary['users']} users, {summary['books']} books, "
                f"{summary['copies']} copies, {summary['loans']} loans "
                f"({summary['overdue']} overdue), "
                f"{summary['pending_requests']} pending requests, "
                f"{summary['approved_posts']} wall posts, "
                f"{summary['announcements']} announcements, "
                f"{summary['audit_logs']} audit logs."
            )
        )
        self.stdout.write(
            "Login with admin / staff / student using DEMO_PASSWORD."
        )
