from django.apps import AppConfig


class DittoPinboardConfig(AppConfig):
    name = 'ditto.pinboard'
    verbose_name = "Ditto Pinboard"

    def ready(self):
        # import myapp.signals
        import ditto.pinboard.checks

