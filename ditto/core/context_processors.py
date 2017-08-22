from .apps import ditto_apps
from ..flickr import app_settings


def ditto(request):
    return {
        'enabled_apps': ditto_apps.enabled(),
        'DITTO_FLICKR_USE_LOCAL_MEDIA':
                                    app_settings.DITTO_FLICKR_USE_LOCAL_MEDIA,
    }

