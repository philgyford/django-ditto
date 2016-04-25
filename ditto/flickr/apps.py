from django.apps import AppConfig


class DittoFlickrConfig(AppConfig):
    name = 'ditto.flickr'
    verbose_name = "Ditto Flickr"

    def ready(self):
        # import ditto.flickr.signals
        import ditto.flickr.checks

