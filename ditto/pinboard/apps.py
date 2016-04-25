from django.apps import AppConfig


class DittoPinboardConfig(AppConfig):
    name = 'ditto.pinboard'
    verbose_name = "Ditto Pinboard"

    def ready(self):
        # import ditto.pinboard.signals
        import ditto.pinboard.checks

