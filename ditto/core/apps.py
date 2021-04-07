# coding: utf-8
from django.apps import apps, AppConfig


class DittoCoreConfig(AppConfig):
    label = "ditto_core"
    name = "ditto.core"
    verbose_name = "Ditto Core"

    # Maintain pre Django 3.2 default behaviour:
    default_auto_field = "django.db.models.AutoField"


class Apps(object):
    """Methods for seeing which Ditto apps are installed/enabled.
    At the moment installed is the same as enabled, but in future we may add
    conditions that mean an installed app can be disabled.

    So use installed to check if the code is physically in INSTALLED_APPS.
    And use enabled to check if we're allowed to use that app on the site.
    """

    def all(self):
        "A list of all possible Ditto apps that could be installed/enabled."
        return [
            "flickr",
            "lastfm",
            "pinboard",
            "twitter",
        ]

    def installed(self):
        "A list of all the installed Ditto apps."
        return [app for app in self.all() if self.is_installed(app)]

    def enabled(self):
        "A list of all the enabled Ditto apps."
        return [app for app in self.all() if self.is_enabled(app)]

    def is_installed(self, app_name):
        "Is this Ditto app installed?"
        return apps.is_installed("ditto.%s" % app_name)

    def is_enabled(self, app_name):
        """Determine if a particular Ditto app is installed and enabled.

        app_name is like 'pinboard' or 'twitter'.

        Usage:
            if is_enabled('pinboard'):
                print("Pinboard is enabled")

        Doesn't offer much over apps.is_installed() yet, but would let us add other
        conditions in future, like being able to enable/disable installed apps.
        """
        return apps.is_installed("ditto.%s" % app_name)


ditto_apps = Apps()
