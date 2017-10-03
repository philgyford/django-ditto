from .apps import ditto_apps
from ..flickr import app_settings


def ditto(request):
    return {
        'enabled_apps': ditto_apps.enabled()
    }

