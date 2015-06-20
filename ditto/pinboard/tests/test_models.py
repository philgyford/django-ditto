from django.test import TestCase

from .. import factories
from ..models import Bookmark


class PinboardAccountTests(TestCase):

    def test_str(self):
        account = factories.AccountFactory(username='bill')
        self.assertEqual(account.__str__(), 'Pinboard: bill')

    def test_service_name(self):
        account = factories.AccountFactory()
        self.assertEqual(account.service_name, 'Pinboard')

class PinboardBookmarkTests(TestCase):

    def test_save(self):
        "Make sure its save() method calls the parent, so actually saves."
        bookmark = factories.BookmarkFactory(title='My title')
        bookmark.save()
        b = Bookmark.objects.get(title='My title')
        self.assertEqual(b.pk, bookmark.pk)

    def test_summary_creation(self):
        "Make sure it creates Item's summary."
        bookmark = factories.BookmarkFactory(description='My description')
        self.assertEqual(bookmark.summary, bookmark.description)

    def test_get_absolute_url(self):
        # TODO
        pass


