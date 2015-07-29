from django.core.urlresolvers import reverse
from django.test import TestCase

from ...pinboard import factories as pinboardfactories


class DittoViewTests(TestCase):

    def test_home_templates(self):
        "Overall home page uses the correct templates"
        response = self.client.get(reverse('ditto:index'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ditto/index.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_home_context(self):
        "Overall home page sends correct data to templates"
        pinboard_accounts = pinboardfactories.AccountFactory.create_batch(3)
        pinboard_bookmarks_1 = pinboardfactories.BookmarkFactory.create_batch(
                                            6, account=pinboard_accounts[0])
        pinboard_bookmarks_2 = pinboardfactories.BookmarkFactory.create_batch(
                                            6, account=pinboard_accounts[1])
        pinboard_bookmark_private = pinboardfactories.BookmarkFactory.create(
                                            account=pinboard_accounts[1],
                                            title='Private bookmark',
                                            is_private=True)
        response = self.client.get(reverse('ditto:index'))

        self.assertTrue('pinboard_bookmark_list' in response.context)
        # It shows 10 of all the bookmarks:
        self.assertEqual(len(response.context['pinboard_bookmark_list']), 5)
        # It doesn't include the most recent one, which is private:
        self.assertNotEqual(
                        response.context['pinboard_bookmark_list'][0].title,
                        'Private bookmark')

    def test_home_privacy(self):
        "Overall home page does not display private Bookmarks etc"
        public_bookmark = pinboardfactories.BookmarkFactory(is_private=False)
        private_bookmark = pinboardfactories.BookmarkFactory(is_private=True)
        response = self.client.get(reverse('ditto:index'))

        self.assertEqual(len(response.context['pinboard_bookmark_list']), 1)
        self.assertTrue(response.context['pinboard_bookmark_list'][0].pk,
                                                            public_bookmark.pk)

    def test_tag_detail_templates(self):
        "Uses the correct templates"
        bookmark = pinboardfactories.BookmarkFactory.create()
        bookmark.tags.set('fish')
        response = self.client.get(reverse('ditto:tag_detail',
                                                    kwargs={'slug': 'fish'}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ditto/tag_detail.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_tag_detail_context(self):
        "Sends correct data to templates"
        bookmark_1 = pinboardfactories.BookmarkFactory.create(title='Carp')
        bookmark_1.tags.set('Fish', 'carp')
        bookmark_2 = pinboardfactories.BookmarkFactory.create(title='Cod')
        bookmark_2.tags.set('Fish', 'cod')
        bookmark_3 = pinboardfactories.BookmarkFactory.create(title='Dog')
        bookmark_3.tags.set('mammals', 'dog')
        response = self.client.get(reverse('ditto:tag_detail',
                                                    kwargs={'slug': 'fish'}))
        self.assertTrue('tag' in response.context)
        self.assertEqual(response.context['tag'].name, 'Fish')
        self.assertTrue('bookmark_list' in response.context)
        self.assertEqual(len(response.context['bookmark_list']), 2)
        self.assertEqual(response.context['bookmark_list'][0].title, 'Cod')
        self.assertEqual(response.context['bookmark_list'][1].title, 'Carp')

    def test_tag_detail_privacy(self):
        "Does not display private bookmarks"
        bookmark_1 = pinboardfactories.BookmarkFactory.create(is_private=True)
        bookmark_1.tags.set('fish')
        bookmark_2 = pinboardfactories.BookmarkFactory.create(is_private=False)
        bookmark_2.tags.set('fish')
        response = self.client.get(reverse('ditto:tag_detail',
                                                    kwargs={'slug': 'fish'}))
        self.assertTrue('bookmark_list' in response.context)
        self.assertEqual(len(response.context['bookmark_list']), 1)
        self.assertEqual(response.context['bookmark_list'][0].pk, bookmark_2.pk)

