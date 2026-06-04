from django.db import migrations, models
from django.utils.text import slugify


def populate_category_slugs(apps, schema_editor):
    Category = apps.get_model("books", "Category")
    for cat in Category.objects.all():
        if not cat.slug:
            cat.slug = slugify(cat.name).replace("-", "_")
            cat.save(update_fields=["slug"])


def add_slug_field(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'books_category' AND column_name = 'slug'
                ) THEN
                    ALTER TABLE books_category ADD COLUMN slug varchar(200);
                END IF;
            END $$;"""
        )


def make_slug_unique(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_class WHERE relname = 'books_category_slug_key'
                ) THEN
                    ALTER TABLE books_category
                    ADD CONSTRAINT books_category_slug_key UNIQUE (slug);
                END IF;
            END $$;"""
        )


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0003_populate_categories"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_slug_field, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="category",
                    name="slug",
                    field=models.SlugField(max_length=200, null=True),
                ),
            ],
        ),
        migrations.RunPython(populate_category_slugs, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(make_slug_unique, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="category",
                    name="slug",
                    field=models.SlugField(max_length=200, unique=True),
                ),
            ],
        ),
    ]
