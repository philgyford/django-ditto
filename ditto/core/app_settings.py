from django.conf import settings


# Creating all the defaults for settings.
# In our code, if we want to use a DITTO_* setting we should import
# from here, not django.conf.settings.

# e.g. "07:34"
CORE_TIME_FORMAT = getattr(settings, "DITTO_CORE_TIME_FORMAT", "%H:%M")

# e.g. "8 Apr 2018"
CORE_DATE_FORMAT = getattr(settings, "DITTO_CORE_DATE_FORMAT", "%-d %b %Y")

# e.g. "07:34 on 8 Apr 2018"
CORE_DATETIME_FORMAT = getattr(
    settings, "DITTO_CORE_DATETIME_FORMAT", "[time] on [date]"
)

# e.g. "2018"
CORE_DATE_YEAR_FORMAT = getattr(settings, "DITTO_CORE_DATE_YEAR_FORMAT", "%Y")

# e.g. "Apr 2018"
CORE_DATE_YEAR_MONTH_FORMAT = getattr(
    settings, "DITTO_CORE_DATE_YEAR_MONTH_FORMAT", "%b %Y"
)
