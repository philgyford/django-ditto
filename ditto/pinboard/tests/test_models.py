from django.test import TestCase

from .. import factories


class PinboardAccountTests(TestCase):

    def test_str(self):
        account = factories.AccountFactory(username='bill')
        self.assertEqual(account.__str__(), 'Pinboard: bill')

    def test_service_name(self):
        account = factories.AccountFactory()
        self.assertEqual(account.service_name, 'Pinboard')

