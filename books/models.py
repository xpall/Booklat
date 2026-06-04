import hashlib

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def book_count(self):
        return self.book_set.filter(is_archived=False).count()

    @property
    def color(self):
        h = hashlib.md5(self.name.encode()).hexdigest()
        hue = int(h[:8], 16) % 360
        return f"hsl({hue}, 60%, 45%)"


class Book(models.Model):
    isbn = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=500)
    subtitle = models.CharField(max_length=500, blank=True)
    authors = models.CharField(max_length=500)
    publisher = models.CharField(max_length=300, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    _categories_text = models.CharField(max_length=500, blank=True, help_text="Comma-separated categories (legacy)")
    categories = models.ManyToManyField(Category, blank=True, related_name="book_set")
    cover_image = models.URLField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title