# coding: utf-8

from django.db import IntegrityError
from django.test import TestCase

from .. import factories
from ..models import Account


class TwitterAccountTestCase(TestCase):

    def test_str(self):
        "The string representation of the Account is correct"
        account = factories.AccountFactory(screen_name='bill')
        self.assertEqual(account.__str__(), 'bill')

    def test_unique_screen_name(self):
        "Ensures that screen_names are unique"
        account_1 = factories.AccountFactory(screen_name='billy')
        with self.assertRaises(IntegrityError):
            account_2 = factories.AccountFactory(screen_name='billy')

    def test_ordering(self):
        """Multiple accounts are ordered alphabetically"""
        account_1 = factories.AccountFactory(screen_name='billy')
        account_2 = factories.AccountFactory(screen_name='amanda')
        accounts = Account.objects.all()
        self.assertEqual(accounts[0].screen_name, 'amanda')

