from django.conf import settings


# Creating all the defaults for settings.
# In our code, if we want to use a DITTO_FLICKR_* setting we should import
# from here, not django.conf.settings.


DITTO_FLICKR_DIR_BASE = getattr(settings, 'DITTO_FLICKR_DIR_BASE', 'flickr')

DITTO_FLICKR_DIR_PHOTOS_FORMAT = getattr(settings,
                                'DITTO_FLICKR_DIR_PHOTOS_FORMAT', '%Y/%m/%d')

DITTO_FLICKR_USE_LOCAL_MEDIA = getattr(settings,
                                        'DITTO_FLICKR_USE_LOCAL_MEDIA', False)

