from .apps import ditto_apps
from ..flickr import app_settings


def ditto(request):
    # Get the name of the current page from the url conf.
    # So we can tell which page we're on in the templates.
    url_name = False
    if request.resolver_match:
        url_name = request.resolver_match.url_name

    return {
        'url_name': url_name,
        'enabled_apps': ditto_apps.enabled(),
        'DITTO_FLICKR_USE_LOCAL_MEDIA':
                                    app_settings.DITTO_FLICKR_USE_LOCAL_MEDIA,
    }

