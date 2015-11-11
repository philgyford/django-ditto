# coding: utf-8
from django.apps import apps


def all():
    "A list of all possible Ditto apps that could be installed/enabled."
    return ['pinboard', 'twitter']

def installed():
    "A list of all the installed Ditto apps."
    return [app for app in all() if is_installed(app)]

def enabled():
    "A list of all the enabled Ditto apps."
    return [app for app in all() if is_enabled(app)]

def is_installed(app_name):
    "Is this Ditto app installed?"
    return apps.is_installed('ditto.%s' % app_name)

def is_enabled(app_name):
    """Determine if a particular Ditto app is installed and enabled.

    app_name is like 'pinboard' or 'twitter'.

    Usage:
        if is_enabled('pinboard'):
            print("Pinboard is enabled")

    Doesn't offer much over apps.is_installed() yet, but would let us add other
    conditions in future, like being able to enable/disable installed apps.
    """
    return apps.is_installed('ditto.%s' % app_name)

