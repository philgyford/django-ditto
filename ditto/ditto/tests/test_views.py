from django.core.urlresolvers import reverse
from django.test import TestCase

from ...pinboard import factories as pinboardfactories


class DittoViewTests(TestCase):

    def test_home_templates(self):
        response = self.client.get(reverse('ditto'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ditto/ditto/index.html')
        self.assertTemplateUsed(response, 'ditto/ditto/base.html')

    def test_home_context(self):
        pinboard_accounts = pinboardfactories.AccountFactory.create_batch(3)
        pinboard_bookmarks_1 = pinboardfactories.BookmarkFactory.create_batch(
                                            6, account=pinboard_accounts[0])
        pinboard_bookmarks_2 = pinboardfactories.BookmarkFactory.create_batch(
                                            6, account=pinboard_accounts[1])
        response = self.client.get(reverse('ditto'))
        self.assertTrue('pinboard_bookmark_list' in response.context)
        # It shows 10 of all the bookmarks:
        self.assertEqual(len(response.context['pinboard_bookmark_list']), 5)


