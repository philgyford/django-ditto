from django.conf import settings


# Creating all the defaults for settings.

DITTO_TWITTER_DIR_BASE = getattr(settings, 'DITTO_TWITTER_DIR_BASE', 'twitter')


