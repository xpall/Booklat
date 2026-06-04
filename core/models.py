from django.db import models


class AboutConfig(models.Model):
    data = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "About Page Config"
        verbose_name_plural = "About Page Config"

    def __str__(self):
        return "About Page Configuration"

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={"data": {"school_years": []}},
        )
        return obj
