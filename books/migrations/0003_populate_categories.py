from django.db import migrations


def populate_categories(apps, schema_editor):
    Book = apps.get_model("books", "Book")
    Category = apps.get_model("books", "Category")

    for book in Book.objects.all():
        text = (book._categories_text or "").strip()
        if not text:
            continue
        names = [n.strip() for n in text.split(",") if n.strip()]
        for name in names:
            category, _ = Category.objects.get_or_create(name=name)
            book.categories.add(category)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0002_category_model"),
    ]

    operations = [
        migrations.RunPython(populate_categories, reverse_code=noop),
    ]
