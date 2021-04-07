from django.apps import AppConfig


class DittoTwitterConfig(AppConfig):
    name = "ditto.twitter"
    verbose_name = "Ditto Twitter"

    # Maintain pre Django 3.2 default behaviour:
    default_auto_field = "django.db.models.AutoField"
