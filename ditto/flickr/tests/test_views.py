from django.core.urlresolvers import reverse
from django.test import TestCase

from .. import factories


class ViewTests(TestCase):

    def test_home_templates(self):
        "The Flickr home page uses the correct templates"
        response = self.client.get(reverse('flickr:index'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'flickr/index.html')
        self.assertTemplateUsed(response, 'flickr/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_home_context(self):
        "The Flickr home page sends the correct data to templates"
        accounts = factories.AccountFactory.create_batch(3)
        photos_1 = factories.PhotoFactory.create_batch(
                                                    2, user=accounts[0].user)
        photos_2 = factories.PhotoFactory.create_batch(
                                                    2, user=accounts[1].user)
        response = self.client.get(reverse('flickr:index'))
        self.assertIn('account_list', response.context)
        self.assertIn('photo_list', response.context)
        # Three accounts, only two of which have Photos:
        self.assertEqual(
            [account.pk for account in response.context['account_list']],
            [1,2,3]
        )
        # Photos for both accounts that have them:
        self.assertEqual(
            [photo.pk for photo in response.context['photo_list']],
            [1,2,3,4]
        )

    def test_home_privacy(self):
        "Only public Photos should appear."
        # We only display Photos from Accounts, so add some.
        user_1 = factories.UserFactory()
        user_2 = factories.UserFactory()
        account_1 = factories.AccountFactory(user=user_1)
        account_2 = factories.AccountFactory(user=user_2)

        public_photo_1 = factories.PhotoFactory(user=user_1)
        private_photo_1 = factories.PhotoFactory(user=user_1, is_private=True)
        public_photo_2 = factories.PhotoFactory(user=user_2)
        private_photo_2 = factories.PhotoFactory(user=user_2, is_private=True)

        response = self.client.get(reverse('flickr:index'))
        photos = response.context['photo_list']
        self.assertEqual(len(photos), 2)
        self.assertEqual(photos[0].pk, public_photo_1.pk)
        self.assertEqual(photos[1].pk, public_photo_2.pk)

