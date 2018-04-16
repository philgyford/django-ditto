from ditto.core import app_settings


def override_app_settings(**test_settings):
    """
    A decorator for overriding settings that takes uses our core.app_settings
    module.

    Because if we use the standard @override_settings decorator that doesn't
    work with our app_settings, which are set before we override them.

    Use like:

        from django.test import TestCase
        from tests.core import override_app_settings

        class MyTestCase(TestCase):

            @override_app_settings(MY_SETTING='hello')
            def test_does_a_thing(self):
                # ...
            
    From https://gist.github.com/integricho/6502772fd3c144c719a7
    """
    def _override_app_settings(func):
        def __override_app_settings(*args, **kwargs):
            old_values = dict()
            for key, value in test_settings.items():
                old_values[key] = getattr(app_settings, key)
                setattr(app_settings, key, value)

            result = func(*args, **kwargs)

            for key, value in test_settings.items():
                setattr(app_settings, key, old_values[key])

            return result
        return __override_app_settings
    return _override_app_settings
