from django.core.urlresolvers import reverse
from django.test import TestCase

from .. import factories


class PinboardViewTests(TestCase):

    def test_home_templates(self):
        response = self.client.get(reverse('pinboard'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/bookmark_list.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/ditto/base.html')

    def test_home_context(self):
        accounts = factories.AccountFactory.create_batch(3)
        bookmarks_1 = factories.BookmarkFactory.create_batch(
                                                    5, account=accounts[0])
        bookmarks_2 = factories.BookmarkFactory.create_batch(
                                                    5, account=accounts[1])
        response = self.client.get(reverse('pinboard'))
        self.assertTrue('account_list' in response.context)
        self.assertTrue('bookmark_list' in response.context)
        # Three accounts, only two of whicih have bookmarks:
        self.assertEqual(
            [account.pk for account in response.context['account_list']],
            [1,2,3]
        )
        # Bookmarks for both accounts that have them:
        self.assertEqual(
            [bookmark.pk for bookmark in response.context['bookmark_list']],
            [10,9,8,7,6,5,4,3,2,1]
        )

    def test_account_detail_templates(self):
        account = factories.AccountFactory.create()
        response = self.client.get(reverse('account_detail',
                                        kwargs={'username': account.username}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/account_detail.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/ditto/base.html')

    def test_account_detail_context(self):
        account_1 = factories.AccountFactory.create()
        account_2 = factories.AccountFactory.create()
        bookmarks_1 = factories.BookmarkFactory.create_batch(
                                                        3, account=account_1)
        bookmarks_2 = factories.BookmarkFactory.create_batch(
                                                        3, account=account_2)
        response = self.client.get(reverse('account_detail',
                                    kwargs={'username': account_1.username}))
        self.assertTrue('account' in response.context)
        self.assertEqual(account_1.pk, response.context['account'].pk)
        self.assertTrue('bookmark_list' in response.context)
        self.assertEqual(len(response.context['bookmark_list']), 3)
        self.assertEqual(
            [bookmark.pk for bookmark in response.context['bookmark_list']],
            [3,2,1]
        )

    def test_account_detail_fails(self):
        account = factories.AccountFactory.create()
        response = self.client.get(reverse('account_detail',
                                        kwargs={'username': 'doesnotexist'}))
        self.assertEquals(response.status_code, 404)

    def test_bookmark_detail_templates(self):
        bookmark = factories.BookmarkFactory.create()
        response = self.client.get(reverse('bookmark_detail',
            kwargs={'username': bookmark.account.username, 'pk': bookmark.pk}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/bookmark_detail.html')

    def test_bookmark_detail_context(self):
        bookmark = factories.BookmarkFactory.create()
        response = self.client.get(reverse('bookmark_detail',
            kwargs={'username': bookmark.account.username, 'pk': bookmark.pk}))
        self.assertTrue('bookmark' in response.context)
        self.assertEqual(bookmark.pk, response.context['bookmark'].pk)

    def test_bookmark_detail_fails(self):
        bookmark = factories.BookmarkFactory.create()
        response = self.client.get(reverse('bookmark_detail',
                    kwargs={'username': bookmark.account.username, 'pk':2}))
        self.assertEquals(response.status_code, 404)

