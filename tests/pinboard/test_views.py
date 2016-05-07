from django.core.urlresolvers import reverse
from django.test import TestCase

from ditto.pinboard.factories import AccountFactory, BookmarkFactory


class PinboardViewTests(TestCase):

    def test_home_templates(self):
        "The Pinboard home page uses the correct templates"
        response = self.client.get(reverse('pinboard:home'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/home.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_home_context(self):
        "The Pinboard home page sends the correct data to templates"
        account_1 = AccountFactory(username='abby')
        account_2 = AccountFactory(username='bobby')
        account_3 = AccountFactory(username='charlie')
        bookmarks_1 = BookmarkFactory.create_batch(5, account=account_1)
        bookmarks_2 = BookmarkFactory.create_batch(5, account=account_2)
        response = self.client.get(reverse('pinboard:home'))
        self.assertIn('account_list', response.context)
        self.assertIn('bookmark_list', response.context)
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
        public_bookmark_1 = BookmarkFactory(is_private=False)
        private_bookmark = BookmarkFactory(is_private=True)
        public_bookmark_2 = BookmarkFactory(is_private=False)
        response = self.client.get(reverse('pinboard:home'))
        bookmarks = response.context['bookmark_list']
        self.assertEqual(len(bookmarks), 2)
        self.assertEqual(bookmarks[0].pk, public_bookmark_2.pk)
        self.assertEqual(bookmarks[1].pk, public_bookmark_1.pk)

    ## TO READ

    def test_to_read_templates(self):
        "The Pinboard 'to read' page uses the correct templates"
        response = self.client.get(reverse('pinboard:toread'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/toread_list.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_to_read_context(self):
        """The Pinboard 'to read' page sends the correct data to templates.
        Also tests privacy."""
        accounts = AccountFactory.create_batch(3)
        bookmarks_1 = BookmarkFactory.create_batch(2, account=accounts[0])
        bookmarks_2 = BookmarkFactory.create_batch(2, account=accounts[1])
        bookmarks_1[0].to_read = True
        bookmarks_1[0].save()
        bookmarks_1[1].to_read = True
        bookmarks_1[1].is_private = True
        bookmarks_1[1].save()
        bookmarks_2[1].to_read = True
        bookmarks_2[1].save()
        response = self.client.get(reverse('pinboard:toread'))
        self.assertIn('account_list', response.context)
        self.assertIn('bookmark_list', response.context)
        # Three accounts, only two of which have bookmarks:
        self.assertEqual(
            [account.pk for account in response.context['account_list']],
            [1,2,3]
        )
        # Bookmarks for both accounts that have them:
        self.assertEqual(
            [bookmark.pk for bookmark in response.context['bookmark_list']],
            [bookmarks_2[1].pk, bookmarks_1[0].pk,]
        )

    ## ACCOUNT DETAIL

    def test_account_detail_templates(self):
        "Uses the correct templates"
        account = AccountFactory()
        response = self.client.get(reverse('pinboard:account_detail',
                                        kwargs={'username': account.username}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/account_detail.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_account_detail_context(self):
        "Sends the correct data to templates"
        account_1 = AccountFactory()
        account_2 = AccountFactory()
        bookmarks_1 = BookmarkFactory.create_batch(3, account=account_1)
        bookmarks_2 = BookmarkFactory.create_batch(3, account=account_2)
        response = self.client.get(reverse('pinboard:account_detail',
                                    kwargs={'username': account_1.username}))
        self.assertIn('account', response.context)
        self.assertEqual(account_1.pk, response.context['account'].pk)
        self.assertIn('bookmark_list', response.context)
        self.assertEqual(len(response.context['bookmark_list']), 3)
        self.assertEqual(
            [bookmark.pk for bookmark in response.context['bookmark_list']],
            [3,2,1]
        )

    def test_account_detail_privacy(self):
        "It does not show private Bookmarks"
        account = AccountFactory()
        public_bookmark = BookmarkFactory(account=account, is_private=False)
        private_bookmark = BookmarkFactory(account=account,is_private=True)
        response = self.client.get(reverse('pinboard:account_detail',
                                        kwargs={'username': account.username}))
        self.assertEqual(len(response.context['bookmark_list']), 1)
        self.assertTrue(response.context['bookmark_list'][0].pk,
                                                            public_bookmark.pk)

    def test_account_detail_fails(self):
        "Requests for non-existent accounts 404"
        account = AccountFactory()
        response = self.client.get(reverse('pinboard:account_detail',
                                        kwargs={'username': 'doesnotexist'}))
        self.assertEquals(response.status_code, 404)

    ## ACCOUNT TO READ

    def test_account_toread_templates(self):
        "Uses the correct templates"
        account = AccountFactory()
        response = self.client.get(reverse('pinboard:account_toread',
                                        kwargs={'username': account.username}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/account_toread.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_account_detail_context(self):
        "Sends the correct data to templates. Also tests privacy."
        accounts = AccountFactory.create_batch(2)
        bookmarks_1 = BookmarkFactory.create_batch(2, account=accounts[0])
        bookmarks_2 = BookmarkFactory.create_batch(2, account=accounts[1])
        bookmarks_1[0].to_read = True
        bookmarks_1[0].save()
        bookmarks_1[1].to_read = True
        bookmarks_1[1].is_private = True
        bookmarks_1[1].save()
        bookmarks_2[1].to_read = True
        bookmarks_2[1].save()

        response = self.client.get(reverse('pinboard:account_toread',
                                    kwargs={'username': accounts[0].username}))
        self.assertIn('account', response.context)
        self.assertEqual(accounts[0].pk, response.context['account'].pk)
        self.assertIn('bookmark_list', response.context)
        self.assertEqual(len(response.context['bookmark_list']), 1)
        self.assertEqual(response.context['bookmark_list'][0].pk,
                                                            bookmarks_1[0].pk)

    ## BOOKMARK DETAIL

    def test_bookmark_detail_templates(self):
        "Uses the correct templates"
        bookmark = BookmarkFactory()
        response = self.client.get(reverse('pinboard:bookmark_detail',
            kwargs={'username': bookmark.account.username,
                    'hash': bookmark.url_hash}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/bookmark_detail.html')

    def test_bookmark_detail_context(self):
        "Sends the correct data to templates"
        bookmark = BookmarkFactory()
        response = self.client.get(reverse('pinboard:bookmark_detail',
            kwargs={'username': bookmark.account.username,
                    'hash': bookmark.url_hash}))
        self.assertIn('bookmark', response.context)
        self.assertEqual(bookmark.pk, response.context['bookmark'].pk)

    def test_bookmark_detail_privacy(self):
        "Does not display private bookmarks"
        bookmark = BookmarkFactory(is_private=True)
        response = self.client.get(reverse('pinboard:bookmark_detail',
            kwargs={'username': bookmark.account.username,
                    'hash': bookmark.url_hash}))
        self.assertEquals(response.status_code, 404)

    def test_bookmark_detail_tag_privacy(self):
        "Does not display private tags"
        bookmark = BookmarkFactory()
        bookmark.tags.set('publictag', '.notpublic', 'alsopublic')
        response = self.client.get(reverse('pinboard:bookmark_detail',
            kwargs={'username': bookmark.account.username,
                    'hash': bookmark.url_hash}))
        # The private/public logic happens in the templates, so check output:
        self.assertIn('publictag', response.content.decode('utf8'))
        self.assertIn('alsopublic', response.content.decode('utf8'))
        self.assertNotIn('.notpublic', response.content.decode('utf8'))

    def test_bookmark_detail_fails(self):
        "Returns a 404 if a non-existent bookmark's page is requested"
        bookmark = BookmarkFactory()
        response = self.client.get(reverse('pinboard:bookmark_detail',
                    kwargs={'username': bookmark.account.username,
                            'hash':'1234567890ab'}))
        self.assertEquals(response.status_code, 404)

    ## TAG LIST

    def test_tag_list_templates(self):
        "Uses the correct templates"
        # Shouldn't need any bookmarks to exist.
        response = self.client.get(reverse('pinboard:tag_list'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/tag_list.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_tag_list_context(self):
        "Sends the correct data to templates"
        bookmark_1 = BookmarkFactory()
        bookmark_1.tags.set('fish', 'carp')
        bookmark_2 = BookmarkFactory()
        bookmark_2.tags.set('fish', 'cod')
        response = self.client.get(reverse('pinboard:tag_list'))
        self.assertIn('tag_list', response.context)
        self.assertEqual(len(response.context['tag_list']), 3)

    def test_tag_list_privacy_bookmarks(self):
        "Doesn't display tags from private bookmarks"
        bookmark_1 = BookmarkFactory(is_private=True)
        bookmark_1.tags.set('fish', 'carp')
        bookmark_2 = BookmarkFactory(is_private=False)
        bookmark_2.tags.set('fish', 'cod')
        response = self.client.get(reverse('pinboard:tag_list'))
        self.assertEqual(len(response.context['tag_list']), 2)
        self.assertEqual(response.context['tag_list'][0].name, 'fish')
        self.assertEqual(response.context['tag_list'][1].name, 'cod')

    def test_tag_list_privacy_tags(self):
        "Doesn't display private .tags"
        bookmark = BookmarkFactory()
        bookmark.tags.set('ispublic', '.notpublic', 'alsopublic')
        response = self.client.get(reverse('pinboard:tag_list'))
        self.assertEqual(len(response.context['tag_list']), 2)
        # Tags on this page are ordered by popularity, so can't be sure
        # which is 'alsopublic' and which is 'ispublic':
        tag_names = [tag.name for tag in response.context['tag_list']]
        self.assertIn('alsopublic', tag_names)
        self.assertIn('ispublic', tag_names)

    ## TAG DETAIL

    def test_tag_detail_templates(self):
        "Uses the correct templates"
        bookmark = BookmarkFactory()
        bookmark.tags.set('fish')
        response = self.client.get(reverse('pinboard:tag_detail',
                                                    kwargs={'slug': 'fish'}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/tag_detail.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_tag_detail_context(self):
        "Sends the correct data to the templates"
        bookmark_1 = BookmarkFactory(title='Carp')
        bookmark_1.tags.set('Fish', 'carp')
        bookmark_2 = BookmarkFactory(title='Cod')
        bookmark_2.tags.set('Fish', 'cod')
        bookmark_3 = BookmarkFactory(title='Dog')
        bookmark_3.tags.set('mammals', 'dog')
        response = self.client.get(reverse('pinboard:tag_detail',
                                                    kwargs={'slug': 'fish'}))

        self.assertIn('account_list', response.context)
        self.assertEqual(
            [account.pk for account in response.context['account_list']],
            [1,2,3]
        )
        self.assertIn('tag', response.context)
        self.assertEqual(response.context['tag'].name, 'Fish')
        self.assertIn('bookmark_list', response.context)
        self.assertEqual(len(response.context['bookmark_list']), 2)
        self.assertEqual(response.context['bookmark_list'][0].title, 'Cod')
        self.assertEqual(response.context['bookmark_list'][1].title, 'Carp')

    def test_tag_detail_privacy(self):
        "Does not display private bookmarks"
        bookmark = BookmarkFactory(is_private=True)
        bookmark.tags.set('fish')
        response = self.client.get(reverse('pinboard:tag_detail',
                                                    kwargs={'slug': 'fish'}))
        self.assertEquals(response.status_code, 404)

    def test_tag_detail_fails(self):
        "Returns a 404 if a non-existent tag's page is requested"
        response = self.client.get(reverse('pinboard:tag_detail',
                                                    kwargs={'slug': 'fish'}))
        self.assertEquals(response.status_code, 404)

    ## ACCOUNT TAG DETAIL

    def test_account_tag_detail_templates(self):
        "Uses the correct templates"
        account = AccountFactory()
        bookmark = BookmarkFactory(account=account, title='Carp')
        bookmark.tags.set('fish', 'carp')
        response = self.client.get(reverse('pinboard:account_tag_detail',
                    kwargs={'username': account.username, 'tag_slug': 'fish'}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/account_tag_detail.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_account_tag_detail_context(self):
        "Sends the correct data to templates"
        account_1 = AccountFactory()
        account_2 = AccountFactory()
        bookmarks_1 = BookmarkFactory.create_batch(3, account=account_1)
        bookmarks_1[0].tags.set('Fish', 'carp')
        bookmarks_1[1].tags.set('Fish', 'cod')
        bookmarks_1[2].tags.set('mammals', 'dog')
        bookmarks_2 = BookmarkFactory.create_batch(3, account=account_2)
        bookmarks_2[0].tags.set('Fish', 'carp')
        bookmarks_2[1].tags.set('Fish', 'cod')
        bookmarks_2[2].tags.set('mammals', 'dog')
        response = self.client.get(reverse('pinboard:account_tag_detail',
                kwargs={'username': account_1.username, 'tag_slug': 'fish'}))

        self.assertIn('account', response.context)
        self.assertEqual(account_1.pk, response.context['account'].pk)
        self.assertIn('tag', response.context)
        self.assertEqual(response.context['tag'].name, 'Fish')
        self.assertIn('bookmark_list', response.context)
        self.assertEqual(len(response.context['bookmark_list']), 2)
        self.assertEqual(
            [bookmark.pk for bookmark in response.context['bookmark_list']],
            [2,1]
        )

    def test_account_tag_detail_privacy(self):
        "Does not display private bookmarks"
        bookmark = BookmarkFactory(is_private=True)
        bookmark.tags.set('fish')
        response = self.client.get(reverse('pinboard:account_tag_detail',
            kwargs={'username': bookmark.account.username, 'tag_slug': 'fish'}))
        self.assertEquals(response.status_code, 404)

    def test_account_tag_detail_fails_1(self):
        "Returns a 404 if a non-existent account is requested"
        bookmark = BookmarkFactory()
        bookmark.tags.set('fish')

        response = self.client.get(reverse('pinboard:account_tag_detail',
                    kwargs={'username': 'doesntexist', 'tag_slug': 'fish'}))
        self.assertEquals(response.status_code, 404)

    def test_account_tag_detail_fails_2(self):
        "Returns a 404 if a non-existent tag is requested"
        account = AccountFactory()
        bookmark = BookmarkFactory(account=account)
        bookmark.tags.set('fish')

        response = self.client.get(reverse('pinboard:account_tag_detail',
                kwargs={'username': account.username, 'tag_slug': 'mammals'}))
        self.assertEquals(response.status_code, 404)

