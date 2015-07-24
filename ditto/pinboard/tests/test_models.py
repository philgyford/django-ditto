# coding: utf-8
import datetime
import pytz

from django.db import IntegrityError
from django.test import TestCase

from .. import factories
from ..models import Account, Bookmark


class PinboardAccountTestCase(TestCase):

    def test_str(self):
        account = factories.AccountFactory(username='bill')
        self.assertEqual(account.__str__(), 'Pinboard: bill')

    def test_service_name(self):
        account = factories.AccountFactory()
        self.assertEqual(account.service_name, 'Pinboard')

    def test_unique_username(self):
        account_1 = factories.AccountFactory(username='billy')
        with self.assertRaises(IntegrityError):
            account_2 = factories.AccountFactory(username='billy')

    def test_unique_url(self):
        account_1 = factories.AccountFactory(url='https://pinboard.in/u:billy')
        with self.assertRaises(IntegrityError):
            account_2 = factories.AccountFactory(
                                            url='https://pinboard.in/u:billy')
    def test_get_absolute_url(self):
        account = factories.AccountFactory(username='billy')
        self.assertEqual(account.get_absolute_url(), '/pinboard/billy')

    def test_ordering(self):
        account_1 = factories.AccountFactory(username='billy')
        account_2 = factories.AccountFactory(username='amanda')
        accounts = Account.objects.all()
        self.assertEqual(accounts[0].username, 'amanda')


class PinboardBookmarkTestCase(TestCase):

    def test_save(self):
        "Make sure its save() method calls the parent, so actually saves."
        bookmark = factories.BookmarkFactory(title='My title')
        bookmark.save()
        b = Bookmark.objects.get(title='My title')
        self.assertEqual(b.pk, bookmark.pk)

    def test_url_constraint(self):
        """url must be unique for an Account's Bookmarks"""
        account = factories.AccountFactory()
        bookmark_1 = factories.BookmarkFactory(
                                account=account, url='http://www.example.com')
        bookmark_1.save()
        with self.assertRaises(IntegrityError):
            bookmark_2 = factories.BookmarkFactory(
                                account=account, url='http://www.example.com')

    def test_url_unconstrained(self):
        """URLs do not have to be unique for different Accounts' Bookmarks"""
        account_1 = factories.AccountFactory()
        bookmark_1 = factories.BookmarkFactory(
                            account=account_1, url='http://www.example.com')
        bookmark_1.save()
        account_2 = factories.AccountFactory()
        try:
            bookmark_2 = factories.BookmarkFactory(
                            account=account_2, url='http://www.example.com')
        except IntegrityError:
            self.fail("It looks like there's a Unique constraint on Bookmark.url, which there shouldn't be.")

    def test_summary_creation(self):
        "Make sure it creates Item's summary correctly."

        self.maxDiff = None
        bookmark = factories.BookmarkFactory(description="""<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis, auctor lacus.</p>

        <p>Fusce ullamcorper nunc vitae tincidunt sodales. Vestibulum sit amet lacus at sem porta porta. Donec fringilla laoreet orci eu porta. Aenean non lacus hendrerit, semper odio a, feugiat orci. Suspendisse potenti.</p>""")

        self.assertEqual(bookmark.summary, u'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis, auctor lacus. Fusce ullamcorper nunc vitae tincidunt sodales.…')

    def test_get_absolute_url(self):
        account = factories.AccountFactory(username='billy')
        bookmark = factories.BookmarkFactory(account=account)
        self.assertEqual(bookmark.get_absolute_url(), '/pinboard/billy/1')

    def test_ordering(self):
        account = factories.AccountFactory(username='billy')
        post_time = datetime.datetime.strptime(
                                    '2015-01-01 12:00:00', "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=pytz.utc)
        bookmark_1 = factories.BookmarkFactory(
                            account=account,
                            post_time=post_time)
        bookmark_2 = factories.BookmarkFactory(
                            account=account,
                            post_time=(post_time + datetime.timedelta(days=1)))
        bookmarks = Bookmark.objects.all()
        # Should be most recent first:
        self.assertEqual(bookmarks[0].pk, bookmark_2.pk)
        self.assertEqual(bookmarks[1].pk, bookmark_1.pk)


