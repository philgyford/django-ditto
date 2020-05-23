from django.conf import settings
from django.core.checks import register, Error, Tags


@register(Tags.compatibility)
def check_taggit_is_installed(app_configs=None, **kwargs):
    checks = []
    try:
        from taggit import models  # noqa: F401

    except ImportError:
        checks.append(
            Error(
                "The django-taggit app is required to use ditto.flickr.",
                hint=("Install django-taggit"),
                id="ditto.flickr.E001",
            )
        )

    if len(checks) == 0:
        if "taggit" not in settings.INSTALLED_APPS:
            checks.append(
                Error(
                    "The django-taggit app must be in INSTALLED_APPS",
                    hint=("Add 'taggit' to INSTALLED_APPS in your settings file."),
                    id="ditto.flickr.E002",
                )
            )

    return checks
