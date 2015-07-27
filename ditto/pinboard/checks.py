from django.apps import apps as camelot_apps
from django.conf import settings
from django.core.checks import register, Error
from django.core.checks import Tags as DjangoTags


class Tags(DjangoTags):
    """Do this if none of the existing tags work for you:
    https://docs.djangoproject.com/en/1.8/ref/checks/#builtin-tags
    """
    required_apps = 'required_apps'


@register(Tags.required_apps)
def check_taggit_is_installed(app_configs=None, **kwargs):
    "Check that django-taggit is installed when using pinboard."
    errors = []
    try:
        from taggit import models

    except ImportError:
        errors.append(
            Error(
                "The django-taggit app is required to use pinboard.",
                hint=("Install django-taggit"),
                # A unique ID so it's easier to find this warning:
                id='pinboard.W001',
            )
        )

    if len(errors) == 0:
        if 'taggit' not in settings.INSTALLED_APPS:
            errors.append(
                Error(
                    "The django-taggit app must be in INSTALLED_APPS",
                    hint=("Add 'taggit' to INSTALLED_APPS "
                            "in your settings file."),
                    # A unique ID so it's easier to find this warning:
                    id='pinboard.W002',
                )
            )

    return errors
