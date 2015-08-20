# coding: utf-8
import datetime
import pytz

from django.db import IntegrityError
from django.test import TestCase

from .. import factories
from ..models import Account, Bookmark


class PinboardAccountTestCase(TestCase):

    def test_str(self):
        """The string representation of the Account is correct"""
        account = factories.AccountFactory(username='bill')
        self.assertEqual(account.__str__(), 'bill')

    def test_unique_username(self):
        """Ensures that usernames are unique"""
        account_1 = factories.AccountFactory(username='billy')
        with self.assertRaises(IntegrityError):
            account_2 = factories.AccountFactory(username='billy')

    def test_unique_url(self):
        """Ensures that Account URLs at Pinboard are unique"""
        account_1 = factories.AccountFactory(url='https://pinboard.in/u:billy')
        with self.assertRaises(IntegrityError):
            account_2 = factories.AccountFactory(
                                            url='https://pinboard.in/u:billy')
    def test_get_absolute_url(self):
        """Has the correct URL on this site"""
        account = factories.AccountFactory(username='billy')
        self.assertEqual(account.get_absolute_url(), '/pinboard/billy')

    def test_ordering(self):
        """Multiple accounts are ordered alphabetically"""
        account_1 = factories.AccountFactory(username='billy')
        account_2 = factories.AccountFactory(username='amanda')
        accounts = Account.objects.all()
        self.assertEqual(accounts[0].username, 'amanda')


class PinboardBookmarkTestCase(TestCase):

    def test_save(self):
        """Calls the parent save() method when saving, so it actually saves"""
        bookmark = factories.BookmarkFactory(title='My title')
        bookmark.save()
        b = Bookmark.objects.get(title='My title')
        self.assertEqual(b.pk, bookmark.pk)

    def test_url_constraint(self):
        """Ensures bookmarks have unique URLs within an Account"""
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
        "Creates the Bookmark's summary correctly"

        self.maxDiff = None
        bookmark = factories.BookmarkFactory(description="""<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis, auctor lacus.</p>

        <p>Fusce ullamcorper nunc vitae tincidunt sodales. Vestibulum sit amet lacus at sem porta porta. Donec fringilla laoreet orci eu porta. Aenean non lacus hendrerit, semper odio a, feugiat orci. Suspendisse potenti.</p>""")

        self.assertEqual(bookmark.summary, u'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis, auctor lacus. Fusce ullamcorper nunc vitae tincidunt sodales.…')

    def test_get_absolute_url(self):
        "Has the correct URL on this site"
        account = factories.AccountFactory(username='billy')
        bookmark = factories.BookmarkFactory(account=account)
        self.assertEqual(bookmark.get_absolute_url(), '/pinboard/billy/1')

    def test_ordering(self):
        "Bookmarks are ordered correctly, most-recently-posted first"
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

    def test_tags(self):
        "Can save and recall tags"
        from taggit.models import Tag
        bookmark = factories.BookmarkFactory()
        bookmark.tags.set('banana', 'cherry', 'apple')
        bookmark_reloaded = Bookmark.objects.get(pk=bookmark.pk)
        self.assertEqual(len(bookmark_reloaded.tags.all()), 3)
        self.assertIsInstance(bookmark_reloaded.tags.first(), Tag)
        self.assertEqual(bookmark_reloaded.tags.names().first(), 'apple')
        self.assertEqual(bookmark_reloaded.tags.all()[0].name, 'apple')
        self.assertEqual(bookmark_reloaded.tags.all()[2].name, 'cherry')

    def test_tags_private(self):
        "Doesn't fetch private tags"
        bookmark = factories.BookmarkFactory()
        bookmark.tags.set('ispublic', '.isprivate', 'alsopublic')
        bookmark_reloaded = Bookmark.objects.get(pk=bookmark.pk)
        self.assertEqual(len(bookmark_reloaded.tags.all()), 2)
        self.assertEqual(bookmark_reloaded.tags.names().first(), 'alsopublic')
        self.assertEqual(bookmark_reloaded.tags.all()[0].name, 'alsopublic')
        self.assertEqual(bookmark_reloaded.tags.all()[1].name, 'ispublic')

    def test_slugs_match_tags_true(self):
        "Returns true if a list of slugs is the same to bookmark's tags"
        bookmark = factories.BookmarkFactory()
        bookmark.tags.set('banana', 'cherry')
        self.assertTrue(bookmark.slugs_match_tags(['cherry', 'banana']))

    def test_slugs_match_tags_false(self):
        "Returns false if a list of slugs is different to bookmark's tags"
        bookmark = factories.BookmarkFactory()
        bookmark.tags.set('banana', 'cherry')
        self.assertFalse(bookmark.slugs_match_tags(['banana', 'apple']))

    def test_default_manager(self):
        "The default manager includes public AND private bookmarks"
        public_bookmark_1 = factories.BookmarkFactory(is_private=False)
        private_bookmark = factories.BookmarkFactory(is_private=True)
        public_bookmark_2 = factories.BookmarkFactory(is_private=False)
        self.assertEqual(len(Bookmark.objects.all()), 3)

    def test_public_manager(self):
        "The public manager does NOT include private bookmarks"
        public_bookmark_1 = factories.BookmarkFactory(is_private=False)
        private_bookmark = factories.BookmarkFactory(is_private=True)
        public_bookmark_2 = factories.BookmarkFactory(is_private=False)
        bookmarks = Bookmark.public_objects.all()
        self.assertEqual(len(bookmarks), 2)
        self.assertEqual(bookmarks[0].pk, public_bookmark_2.pk)
        self.assertEqual(bookmarks[1].pk, public_bookmark_1.pk)
