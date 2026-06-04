import random
from django.db import models
from django.conf import settings


class FreedomPost(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        DELETED = "deleted", "Deleted"

    STICKY_COLORS = [
        ("yellow", "Yellow"),
        ("pink", "Pink"),
        ("blue", "Blue"),
        ("green", "Green"),
        ("orange", "Orange"),
        ("purple", "Purple"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="freedom_posts",
    )
    pen_name = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    color = models.CharField(max_length=20, choices=STICKY_COLORS)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_freedom_posts",
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"FreedomPost #{self.pk} by {self.user.lrn} ({self.status})"

    def randomize_color(self):
        self.color = random.choice([c[0] for c in self.STICKY_COLORS])


class FreedomPostUpvote(models.Model):
    post = models.ForeignKey(
        FreedomPost,
        on_delete=models.CASCADE,
        related_name="upvotes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="freedom_upvotes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Upvote by {self.user.lrn} on FreedomPost #{self.post_id}"
