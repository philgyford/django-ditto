from django.apps import AppConfig


class DittoPinboardConfig(AppConfig):
    name = "ditto.pinboard"
    verbose_name = "Ditto Pinboard"

    # Maintain pre Django 3.2 default behaviour:
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        # import ditto.pinboard.signals
        import ditto.pinboard.checks  # noqa: F401
