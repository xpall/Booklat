from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="DROP TABLE IF EXISTS core_librarian CASCADE",
                ),
            ],
            state_operations=[
                migrations.DeleteModel(
                    name="Librarian",
                ),
            ],
        ),
        migrations.CreateModel(
            name="AboutConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data", models.JSONField(default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "About Page Config",
                "verbose_name_plural": "About Page Config",
            },
        ),
    ]
