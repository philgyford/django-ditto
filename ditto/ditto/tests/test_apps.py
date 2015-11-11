# coding: utf-8
from unittest.mock import call, patch

from django.test import TestCase
from django.apps import apps

from ..apps import ditto_apps


class DittoAppsTestCase(TestCase):

    def test_all(self):
        all_apps = ditto_apps.all()
        self.assertEqual(2, len(all_apps))
        self.assertEqual(all_apps[0], 'pinboard')
        self.assertEqual(all_apps[1], 'twitter')

    @patch('ditto.ditto.apps.Apps.all')
    def test_installed(self, patched_all):
        # all() will return an app that is not installed:
        patched_all.return_value = ['pinboard', 'twitter', 'NOPE',]

        # So 'NOPE' shouldn't be returned here:
        installed_apps = ditto_apps.installed()
        self.assertEqual(2, len(installed_apps))
        self.assertEqual(installed_apps[0], 'pinboard')
        self.assertEqual(installed_apps[1], 'twitter')

    @patch('ditto.ditto.apps.Apps.all')
    def test_enabled(self, patched_all):
        # all() will return an app that is not installed:
        patched_all.return_value = ['pinboard', 'twitter', 'NOPE',]

        # So 'NOPE' shouldn't be returned here:
        enabled_apps = ditto_apps.enabled()
        self.assertEqual(2, len(enabled_apps))
        self.assertEqual(enabled_apps[0], 'pinboard')
        self.assertEqual(enabled_apps[1], 'twitter')

    def test_is_installed(self):
        self.assertTrue(ditto_apps.is_installed('pinboard'))
        self.assertFalse(ditto_apps.is_installed('NOPE'))

    def test_is_enabled(self):
        self.assertTrue(ditto_apps.is_enabled('pinboard'))
        self.assertFalse(ditto_apps.is_enabled('NOPE'))

