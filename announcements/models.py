from django.db import models
from django.conf import settings
from django.utils import timezone


class Announcement(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="announcements",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Announcement #{self.pk}: {self.title} ({self.status})"

    def archive(self, actor):
        self.status = self.Status.ARCHIVED
        self.save(update_fields=["status", "updated_at"])
