from django.apps import AppConfig


class DittoFlickrConfig(AppConfig):
    name = "ditto.flickr"
    verbose_name = "Ditto Flickr"

    # Maintain pre Django 3.2 default behaviour:
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        # import ditto.flickr.signals
        import ditto.flickr.checks  # noqa: F401
