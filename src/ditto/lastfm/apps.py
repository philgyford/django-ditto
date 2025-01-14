from django.apps import AppConfig


class DittoLastfmConfig(AppConfig):
    name = "ditto.lastfm"
    verbose_name = "Ditto Last.fm"

    # Maintain pre Django 3.2 default behaviour:
    default_auto_field = "django.db.models.AutoField"
