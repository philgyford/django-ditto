# coding: utf-8
import datetime
import pytz

from django.test import TestCase

from ditto.pinboard.factories import AccountFactory, BookmarkFactory
from ditto.pinboard.templatetags import ditto_pinboard


class TemplatetagsRecentBookmarksTestCase(TestCase):

    def setUp(self):
        account_1 = AccountFactory(username='terry')
        account_2 = AccountFactory(username='bob')
        self.bookmarks_1 = BookmarkFactory.create_batch(6, account=account_1)
        self.bookmarks_2 = BookmarkFactory.create_batch(6, account=account_2)
        self.bookmarks_1[5].is_private = True
        self.bookmarks_1[5].save()

    def test_recent_bookmarks(self):
        "Returns recent public bookmarks from all accounts."
        bookmarks = ditto_pinboard.recent_bookmarks()
        self.assertEqual(10, len(bookmarks))
        # bookmarks[6] would be self.bookmarks_1[5] if [5] wasn't private.
        self.assertEqual(bookmarks[6].pk, self.bookmarks_1[4].pk)

    def test_recent_bookmarks_account(self):
        "Only fetches recent public bookmarks from the named account."
        bookmarks = ditto_pinboard.recent_bookmarks(account='terry')
        self.assertEqual(5, len(bookmarks))
        self.assertEqual(bookmarks[0].pk, self.bookmarks_1[4].pk)

    def test_recent_bookmarks_limit(self):
        bookmarks = ditto_pinboard.recent_bookmarks(limit=8)
        self.assertEqual(8, len(bookmarks))
        self.assertEqual(bookmarks[6].pk, self.bookmarks_1[4].pk)


class TemplatetagsDayBookmarksTestCase(TestCase):

    def setUp(self):
        account_1 = AccountFactory(username='terry')
        account_2 = AccountFactory(username='bob')
        self.bookmarks_1 = BookmarkFactory.create_batch(6, account=account_1)
        self.bookmarks_2 = BookmarkFactory.create_batch(6, account=account_2)

        post_time = datetime.datetime(2015, 3, 18, 12, 0, 0).replace(
                                                            tzinfo=pytz.utc)
        self.bookmarks_1[3].post_time = post_time
        self.bookmarks_1[3].save()
        self.bookmarks_1[5].is_private = True
        self.bookmarks_1[5].post_time = post_time + datetime.timedelta(hours=1)
        self.bookmarks_1[5].save()
        self.bookmarks_2[4].post_time = post_time + datetime.timedelta(hours=2)
        self.bookmarks_2[4].save()

    def test_day_bookmarks(self):
        "Returns public bookmarks from all accounts."
        bookmarks = ditto_pinboard.day_bookmarks(datetime.date(2015, 3, 18))
        self.assertEqual(2, len(bookmarks))
        self.assertEqual(bookmarks[1].pk, self.bookmarks_1[3].pk)

    def test_day_bookmarks_account(self):
        "Only fetches public bookmarks from the named account."
        bookmarks = ditto_pinboard.day_bookmarks(datetime.date(2015, 3, 18),
                                                            account='terry')
        self.assertEqual(1, len(bookmarks))
        self.assertEqual(bookmarks[0].pk, self.bookmarks_1[3].pk)

    def test_day_bookmarks_none(self):
        "Fetches no bookmarks when there aren't any on supplied date."
        bookmarks = ditto_pinboard.recent_bookmarks(datetime.date(2015, 3, 19))
        self.assertEqual(0, len(bookmarks))

