from django.conf import settings


# Creating all the defaults for settings.
# In our code, if we want to use a DITTO_TWITTER_* setting we should import
# from here, not django.conf.settings.

TWITTER_DIR_BASE = getattr(settings, "DITTO_TWITTER_DIR_BASE", "twitter")

TWITTER_USE_LOCAL_MEDIA = getattr(settings, "DITTO_TWITTER_USE_LOCAL_MEDIA", False)
