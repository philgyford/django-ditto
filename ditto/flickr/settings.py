from django.conf import settings


# Creating all the defaults for settings.

DITTO_FLICKR_DIR_BASE = getattr(settings, 'DITTO_FLICKR_DIR_BASE', 'flickr')

DITTO_FLICKR_DIR_PHOTOS_FORMAT = getattr(settings,
                                'DITTO_FLICKR_DIR_PHOTOS_FORMAT', '%Y/%m/%d')

