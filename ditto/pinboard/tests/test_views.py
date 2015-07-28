from django.core.urlresolvers import reverse
from django.test import TestCase

from .. import factories


class PinboardViewTests(TestCase):

    def test_home_templates(self):
        "The Pinboard home page uses the correct templates"
        response = self.client.get(reverse('pinboard:index'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/bookmark_list.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/ditto/base.html')

    def test_home_context(self):
        "The Pinboard home page sends the correct data to templates"
        accounts = factories.AccountFactory.create_batch(3)
        bookmarks_1 = factories.BookmarkFactory.create_batch(
                                                    5, account=accounts[0])
        bookmarks_2 = factories.BookmarkFactory.create_batch(
                                                    5, account=accounts[1])
        response = self.client.get(reverse('pinboard:index'))
        self.assertTrue('account_list' in response.context)
        self.assertTrue('bookmark_list' in response.context)
        # Three accounts, only two of which have bookmarks:
        self.assertEqual(
            [account.pk for account in response.context['account_list']],
            [1,2,3]
        )
        # Bookmarks for both accounts that have them:
        self.assertEqual(
            [bookmark.pk for bookmark in response.context['bookmark_list']],
            [10,9,8,7,6,5,4,3,2,1]
        )

    def test_home_privacy(self):
        """Only public bookmarks should appear."""
        public_bookmark_1 = factories.BookmarkFactory(is_private=False)
        private_bookmark = factories.BookmarkFactory(is_private=True)
        public_bookmark_2 = factories.BookmarkFactory(is_private=False)
        response = self.client.get(reverse('pinboard:index'))
        bookmarks = response.context['bookmark_list']
        self.assertEqual(len(bookmarks), 2)
        self.assertEqual(bookmarks[0].pk, public_bookmark_2.pk)
        self.assertEqual(bookmarks[1].pk, public_bookmark_1.pk)

    def test_account_detail_templates(self):
        "Uses the correct templates"
        account = factories.AccountFactory.create()
        response = self.client.get(reverse('pinboard:account_detail',
                                        kwargs={'username': account.username}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/account_detail.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/ditto/base.html')

    def test_account_detail_context(self):
        "Sends the correct data to templates"
        account_1 = factories.AccountFactory.create()
        account_2 = factories.AccountFactory.create()
        bookmarks_1 = factories.BookmarkFactory.create_batch(
                                                        3, account=account_1)
        bookmarks_2 = factories.BookmarkFactory.create_batch(
                                                        3, account=account_2)
        response = self.client.get(reverse('pinboard:account_detail',
                                    kwargs={'username': account_1.username}))
        self.assertTrue('account' in response.context)
        self.assertEqual(account_1.pk, response.context['account'].pk)
        self.assertTrue('bookmark_list' in response.context)
        self.assertEqual(len(response.context['bookmark_list']), 3)
        self.assertEqual(
            [bookmark.pk for bookmark in response.context['bookmark_list']],
            [3,2,1]
        )

    def test_account_detail_privacy(self):
        "It does not show private Bookmarks"
        account = factories.AccountFactory.create()
        public_bookmark = factories.BookmarkFactory(
                                            account=account, is_private=False)
        private_bookmark = factories.BookmarkFactory(
                                            account=account,is_private=True)
        response = self.client.get(reverse('pinboard:account_detail',
                                        kwargs={'username': account.username}))
        self.assertEqual(len(response.context['bookmark_list']), 1)
        self.assertTrue(response.context['bookmark_list'][0].pk,
                                                            public_bookmark.pk)

    def test_account_detail_fails(self):
        "Requests for non-existent accounts 404"
        account = factories.AccountFactory.create()
        response = self.client.get(reverse('pinboard:account_detail',
                                        kwargs={'username': 'doesnotexist'}))
        self.assertEquals(response.status_code, 404)

    def test_bookmark_detail_templates(self):
        "Uses the correct templates"
        bookmark = factories.BookmarkFactory.create()
        response = self.client.get(reverse('pinboard:bookmark_detail',
            kwargs={'username': bookmark.account.username, 'pk': bookmark.pk}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/bookmark_detail.html')

    def test_bookmark_detail_context(self):
        "Sends the correct data to templates"
        bookmark = factories.BookmarkFactory.create()
        response = self.client.get(reverse('pinboard:bookmark_detail',
            kwargs={'username': bookmark.account.username, 'pk': bookmark.pk}))
        self.assertTrue('bookmark' in response.context)
        self.assertEqual(bookmark.pk, response.context['bookmark'].pk)

    def test_bookmark_detail_privacy(self):
        "Does not display private bookmarks"
        bookmark = factories.BookmarkFactory.create(is_private=True)
        response = self.client.get(reverse('pinboard:bookmark_detail',
            kwargs={'username': bookmark.account.username, 'pk': bookmark.pk}))
        self.assertEquals(response.status_code, 404)

    def test_bookmark_detail_fails(self):
        "Returns a 404 if a non-existent bookmark's page is requested"
        bookmark = factories.BookmarkFactory.create()
        response = self.client.get(reverse('pinboard:bookmark_detail',
                    kwargs={'username': bookmark.account.username, 'pk':2}))
        self.assertEquals(response.status_code, 404)

    def test_tag_list_templates(self):
        "Uses the correct templates"
        # Shouldn't need any bookmarks to exist.
        response = self.client.get(reverse('pinboard:tag_list'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/tag_list.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/ditto/base.html')

    def test_tag_list_context(self):
        "Sends the correct data to templates"
        bookmark_1 = factories.BookmarkFactory.create()
        bookmark_1.tags.set('fish', 'carp')
        bookmark_2 = factories.BookmarkFactory.create()
        bookmark_2.tags.set('fish', 'cod')
        response = self.client.get(reverse('pinboard:tag_list'))
        self.assertTrue('tag_list' in response.context)
        self.assertEqual(len(response.context['tag_list']), 3)

    def test_tag_list_privacy(self):
        "Doesn't display tags from private bookmarks"
        bookmark_1 = factories.BookmarkFactory.create(is_private=True)
        bookmark_1.tags.set('fish', 'carp')
        bookmark_2 = factories.BookmarkFactory.create(is_private=False)
        bookmark_2.tags.set('fish', 'cod')
        response = self.client.get(reverse('pinboard:tag_list'))
        self.assertEqual(len(response.context['tag_list']), 2)
        self.assertEqual(response.context['tag_list'][0].name, 'fish')
        self.assertEqual(response.context['tag_list'][1].name, 'cod')

    def test_tag_detail_templates(self):
        "Uses the correct templates"
        bookmark = factories.BookmarkFactory.create()
        bookmark.tags.set('fish')
        response = self.client.get(reverse('pinboard:tag_detail',
                                                    kwargs={'slug': 'fish'}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/tag_detail.html')

    def test_tag_detail_context(self):
        "Sends the correct data to the templates"
        bookmark_1 = factories.BookmarkFactory.create(title='Carp')
        bookmark_1.tags.set('Fish', 'carp')
        bookmark_2 = factories.BookmarkFactory.create(title='Cod')
        bookmark_2.tags.set('Fish', 'cod')
        bookmark_3 = factories.BookmarkFactory.create(title='Dog')
        bookmark_3.tags.set('mammals', 'dog')
        response = self.client.get(reverse('pinboard:tag_detail',
                                                    kwargs={'slug': 'fish'}))

        self.assertTrue('account_list' in response.context)
        self.assertEqual(
            [account.pk for account in response.context['account_list']],
            [1,2,3]
        )
        self.assertTrue('tag' in response.context)
        self.assertEqual(response.context['tag'].name, 'Fish')
        self.assertTrue('bookmark_list' in response.context)
        self.assertEqual(len(response.context['bookmark_list']), 2)
        self.assertEqual(response.context['bookmark_list'][0].title, 'Cod')
        self.assertEqual(response.context['bookmark_list'][1].title, 'Carp')

    def test_tag_detail_privacy(self):
        "Does not display private bookmarks"
        bookmark = factories.BookmarkFactory.create(is_private=True)
        bookmark.tags.set('fish')
        response = self.client.get(reverse('pinboard:tag_detail',
                                                    kwargs={'slug': 'fish'}))
        self.assertEquals(response.status_code, 404)

    def test_tag_detail_fails(self):
        "Returns a 404 if a non-existent tag's page is requested"
        response = self.client.get(reverse('pinboard:tag_detail',
                                                    kwargs={'slug': 'fish'}))
        self.assertEquals(response.status_code, 404)

    def test_account_tag_detail_templates(self):
        "Uses the correct templates"
        account = factories.AccountFactory.create()
        bookmark = factories.BookmarkFactory.create(
                                                account=account, title='Carp')
        bookmark.tags.set('fish', 'carp')
        response = self.client.get(reverse('pinboard:account_tag_detail',
                    kwargs={'username': account.username, 'tag_slug': 'fish'}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/account_tag_detail.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/ditto/base.html')

    def test_account_tag_detail_context(self):
        "Sends the correct data to templates"
        account_1 = factories.AccountFactory.create()
        account_2 = factories.AccountFactory.create()
        bookmarks_1 = factories.BookmarkFactory.create_batch(
                                                        3, account=account_1)
        bookmarks_1[0].tags.set('Fish', 'carp')
        bookmarks_1[1].tags.set('Fish', 'cod')
        bookmarks_1[2].tags.set('mammals', 'dog')
        bookmarks_2 = factories.BookmarkFactory.create_batch(
                                                        3, account=account_2)
        bookmarks_2[0].tags.set('Fish', 'carp')
        bookmarks_2[1].tags.set('Fish', 'cod')
        bookmarks_2[2].tags.set('mammals', 'dog')
        response = self.client.get(reverse('pinboard:account_tag_detail',
                kwargs={'username': account_1.username, 'tag_slug': 'fish'}))

        self.assertTrue('account' in response.context)
        self.assertEqual(account_1.pk, response.context['account'].pk)
        self.assertTrue('tag' in response.context)
        self.assertEqual(response.context['tag'].name, 'Fish')
        self.assertTrue('bookmark_list' in response.context)
        self.assertEqual(len(response.context['bookmark_list']), 2)
        self.assertEqual(
            [bookmark.pk for bookmark in response.context['bookmark_list']],
            [2,1]
        )

    def test_account_tag_detail_privacy(self):
        "Does not display private bookmarks"
        bookmark = factories.BookmarkFactory.create(is_private=True)
        bookmark.tags.set('fish')
        response = self.client.get(reverse('pinboard:account_tag_detail',
            kwargs={'username': bookmark.account.username, 'tag_slug': 'fish'}))
        self.assertEquals(response.status_code, 404)

    def test_account_tag_detail_fails_1(self):
        "Returns a 404 if a non-existent account is requested"
        bookmark = factories.BookmarkFactory.create()
        bookmark.tags.set('fish')

        response = self.client.get(reverse('pinboard:account_tag_detail',
                    kwargs={'username': 'doesntexist', 'tag_slug': 'fish'}))
        self.assertEquals(response.status_code, 404)

    def test_account_tag_detail_fails_2(self):
        "Returns a 404 if a non-existent tag is requested"
        account = factories.AccountFactory.create()
        bookmark = factories.BookmarkFactory.create(account=account)
        bookmark.tags.set('fish')

        response = self.client.get(reverse('pinboard:account_tag_detail',
                kwargs={'username': account.username, 'tag_slug': 'mammals'}))
        self.assertEquals(response.status_code, 404)

