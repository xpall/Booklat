from django.db import models
from books.models import Book


class BookCopy(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        BORROWED = "borrowed", "Borrowed"
        RESERVED = "reserved", "Reserved"
        LOST = "lost", "Lost"
        DAMAGED = "damaged", "Damaged"
        UNDER_REPAIR = "under_repair", "Under Repair"
        ARCHIVED = "archived", "Archived"

    copy_id = models.CharField(max_length=20, unique=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="copies")
    acquisition_date = models.DateField(null=True, blank=True)
    shelf_location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["copy_id"]

    def __str__(self):
        return f"{self.book.title} — {self.copy_id}"


class CopyHistory(models.Model):
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name="history")
    timestamp = models.DateTimeField(auto_now_add=True)
    event = models.CharField(max_length=100)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name_plural = "Copy histories"

    def __str__(self):
        return f"{self.book_copy.copy_id} — {self.event} at {self.timestamp:%Y-%m-%d %H:%M}"