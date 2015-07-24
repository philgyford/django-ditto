from django.core.urlresolvers import reverse
from django.test import TestCase

from .. import factories


class PinboardViewTests(TestCase):

    def test_home(self):
        bookmarks = factories.BookmarkFactory.create_batch(10)
        response = self.client.get(reverse('pinboard'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/bookmark_list.html')
        self.assertTemplateUsed(response, 'pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/ditto/base.html')
        self.assertTrue('bookmark_list' in response.context)
        self.assertEqual(
            [bookmark.pk for bookmark in response.context['bookmark_list']],
            [1,2,3,4,5,6,7,8,9,10]
        )

    def test_bookmark_detail(self):
        bookmark = factories.BookmarkFactory.create()
        response = self.client.get(reverse('bookmark_detail',
            kwargs={'username': bookmark.account.username, 'pk': bookmark.pk}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pinboard/bookmark_detail.html')
        self.assertTrue('bookmark' in response.context)
        self.assertEqual(bookmark.pk, response.context['bookmark'].pk)

    def test_bookmark_detail_fails(self):
        bookmark = factories.BookmarkFactory.create()
        response = self.client.get(reverse('bookmark_detail',
                    kwargs={'username': bookmark.account.username, 'pk':2}))
        self.assertEquals(response.status_code, 404)

