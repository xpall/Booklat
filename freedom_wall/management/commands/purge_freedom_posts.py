from django.core.management.base import BaseCommand
from freedom_wall.models import FreedomPost
from core.utils import log_action


class Command(BaseCommand):
    help = "Permanently delete all freedom wall posts and upvotes."

    def handle(self, **options):
        count, _ = FreedomPost.objects.all().delete()
        log_action(
            actor=None,
            action="FREEDOM_WALL_PURGED",
            resource_type="FreedomPost",
            resource_id="all",
            metadata={"deleted_count": count, "trigger": "management_command"},
        )
        self.stdout.write(self.style.SUCCESS(f"Purged {count} freedom wall posts."))
