from datetime import date, datetime, timedelta, timezone

from django.test import TestCase

from ditto.core.utils import datetime_from_str
from ditto.pinboard.factories import AccountFactory, BookmarkFactory
from ditto.pinboard.templatetags import ditto_pinboard


class TemplatetagsRecentBookmarksTestCase(TestCase):
    def setUp(self):
        account_1 = AccountFactory(username="terry")
        account_2 = AccountFactory(username="bob")
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
        bookmarks = ditto_pinboard.recent_bookmarks(account="terry")
        self.assertEqual(5, len(bookmarks))
        self.assertEqual(bookmarks[0].pk, self.bookmarks_1[4].pk)

    def test_recent_bookmarks_limit(self):
        bookmarks = ditto_pinboard.recent_bookmarks(limit=8)
        self.assertEqual(8, len(bookmarks))
        self.assertEqual(bookmarks[6].pk, self.bookmarks_1[4].pk)


class TemplatetagsDayBookmarksTestCase(TestCase):
    def setUp(self):
        account_1 = AccountFactory(username="terry")
        account_2 = AccountFactory(username="bob")
        self.bookmarks_1 = BookmarkFactory.create_batch(6, account=account_1)
        self.bookmarks_2 = BookmarkFactory.create_batch(6, account=account_2)

        post_time = datetime(2015, 3, 18, 12, 0, 0, tzinfo=timezone.utc)
        self.bookmarks_1[3].post_time = post_time
        self.bookmarks_1[3].save()
        self.bookmarks_1[5].is_private = True
        self.bookmarks_1[5].post_time = post_time + timedelta(hours=1)
        self.bookmarks_1[5].save()
        self.bookmarks_2[4].post_time = post_time + timedelta(hours=2)
        self.bookmarks_2[4].save()

    def test_day_bookmarks(self):
        "Returns public bookmarks from all accounts."
        bookmarks = ditto_pinboard.day_bookmarks(date(2015, 3, 18))
        self.assertEqual(2, len(bookmarks))
        self.assertEqual(bookmarks[1].pk, self.bookmarks_1[3].pk)

    def test_day_bookmarks_account(self):
        "Only fetches public bookmarks from the named account."
        bookmarks = ditto_pinboard.day_bookmarks(date(2015, 3, 18), account="terry")
        self.assertEqual(1, len(bookmarks))
        self.assertEqual(bookmarks[0].pk, self.bookmarks_1[3].pk)

    def test_day_bookmarks_none(self):
        "Fetches no bookmarks when there aren't any on supplied date."
        bookmarks = ditto_pinboard.recent_bookmarks(date(2015, 3, 19))
        self.assertEqual(0, len(bookmarks))


class AnnualBookmarkCountsTestCase(TestCase):
    def setUp(self):
        account_1 = AccountFactory(username="terry")
        account_2 = AccountFactory(username="bob")
        # Bookmarks in 2015 and 2016 for account_1:
        BookmarkFactory.create_batch(
            3, post_time=datetime_from_str("2015-01-01 12:00:00"), account=account_1
        )
        BookmarkFactory.create_batch(
            2, post_time=datetime_from_str("2016-01-01 12:00:00"), account=account_1
        )
        # And one for account_2 in 2015:
        BookmarkFactory(
            account=account_2, post_time=datetime_from_str("2015-01-01 12:00:00")
        )
        # And one private bookmark for account_1 in 2015:
        BookmarkFactory(
            account=account_1,
            is_private=True,
            post_time=datetime_from_str("2015-01-01 12:00:00"),
        )

    def test_response(self):
        "Returns correct data for all users."
        bookmarks = ditto_pinboard.annual_bookmark_counts()
        self.assertEqual(len(bookmarks), 2)
        self.assertEqual(bookmarks[0]["year"], 2015)
        self.assertEqual(bookmarks[0]["count"], 4)
        self.assertEqual(bookmarks[1]["year"], 2016)
        self.assertEqual(bookmarks[1]["count"], 2)

    def test_response_for_user(self):
        "Returns correct data for one user."
        bookmarks = ditto_pinboard.annual_bookmark_counts(account="terry")
        self.assertEqual(len(bookmarks), 2)
        self.assertEqual(bookmarks[0]["year"], 2015)
        self.assertEqual(bookmarks[0]["count"], 3)
        self.assertEqual(bookmarks[1]["year"], 2016)
        self.assertEqual(bookmarks[1]["count"], 2)

    def test_empty_years(self):
        "It should include years for which there are no bookmarks."
        # Add a photo in 2018, leaving a gap for 2017:
        BookmarkFactory(post_time=datetime_from_str("2018-01-01 12:00:00"))
        bookmarks = ditto_pinboard.annual_bookmark_counts()
        self.assertEqual(len(bookmarks), 4)
        self.assertEqual(bookmarks[2]["year"], 2017)
        self.assertEqual(bookmarks[2]["count"], 0)


class PopularBookmarkTagsTestCase(TestCase):
    def test_tags(self):
        "Contains the correct data"
        bookmark_1 = BookmarkFactory()
        bookmark_1.tags.set(["fish", "carp"])
        bookmark_2 = BookmarkFactory()
        bookmark_2.tags.set(["fish", "cod"])
        tags = ditto_pinboard.popular_bookmark_tags()
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0].name, "fish")
        self.assertEqual(tags[0].num_times, 2)
        self.assertEqual(tags[1].name, "carp")
        self.assertEqual(tags[1].num_times, 1)
        self.assertEqual(tags[2].name, "cod")
        self.assertEqual(tags[2].num_times, 1)

    def test_tags_privacy_bookmarks(self):
        "Doesn't display tags from private bookmarks"
        bookmark_1 = BookmarkFactory(is_private=True)
        bookmark_1.tags.set(["fish", "carp"])
        bookmark_2 = BookmarkFactory(is_private=False)
        bookmark_2.tags.set(["fish", "cod"])
        tags = ditto_pinboard.popular_bookmark_tags()
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0].name, "fish")
        self.assertEqual(tags[0].num_times, 1)
        self.assertEqual(tags[1].name, "cod")
        self.assertEqual(tags[1].num_times, 1)

    def test_tags_privacy_tags(self):
        "Doesn't display private .tags"
        bookmark = BookmarkFactory()
        bookmark.tags.set(["ispublic", ".notpublic", "alsopublic"])
        tags = ditto_pinboard.popular_bookmark_tags()
        self.assertEqual(len(tags), 2)
        # Tags are ordered by popularity, so can't be sure
        # which is 'alsopublic' and which is 'ispublic':
        tag_names = [tag.name for tag in tags]
        self.assertIn("alsopublic", tag_names)
        self.assertIn("ispublic", tag_names)

    def test_tags_limit_default(self):
        "It should return 10 tags by default"
        bookmark = BookmarkFactory()
        bookmark.tags.set(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"])
        tags = ditto_pinboard.popular_bookmark_tags()
        self.assertEqual(len(tags), 10)

    def test_tags_limit_custom(self):
        "It should return `limit` tags"
        bookmark = BookmarkFactory()
        bookmark.tags.set(["1", "2", "3", "4", "5"])
        tags = ditto_pinboard.popular_bookmark_tags(limit=3)
        self.assertEqual(len(tags), 3)
