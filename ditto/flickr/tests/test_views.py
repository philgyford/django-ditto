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

    def test_user_detail_templates(self):
        "Uses the correct templates"
        account = factories.AccountFactory()
        response = self.client.get(reverse('flickr:user_detail',
                                        kwargs={'nsid': account.user.nsid}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'flickr/user_detail.html')
        self.assertTemplateUsed(response, 'flickr/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_user_detail_context_no_account(self):
        "Sends correct data to templates for a User with no Account."
        user = factories.UserFactory()
        users_photos = factories.PhotoFactory.create_batch(2, user=user)
        other_photos = factories.PhotoFactory.create_batch(2)

        response = self.client.get(reverse('flickr:user_detail',
                                                kwargs={'nsid': user.nsid}))
        self.assertIn('account', response.context)
        self.assertIsNone(response.context['account'])

        self.assertIn('flickr_user', response.context)
        self.assertEqual(user.pk, response.context['flickr_user'].pk)

        self.assertIn('photo_list', response.context)
        self.assertEqual(len(response.context['photo_list']), 2)
        # ie, only user's photos.
        self.assertIn(users_photos[0], response.context['photo_list'])
        self.assertIn(users_photos[1], response.context['photo_list'])

    def test_user_detail_context_with_account(self):
        "Sends correct data to templates for a User with an Account."
        user = factories.UserFactory()
        account = factories.AccountFactory(user=user)
        users_photos = factories.PhotoFactory.create_batch(2, user=user)
        other_photos = factories.PhotoFactory.create_batch(2)

        response = self.client.get(reverse('flickr:user_detail',
                                                kwargs={'nsid': user.nsid}))
        self.assertIn('account', response.context)
        self.assertEqual(response.context['account'], account)

        self.assertIn('flickr_user', response.context)
        self.assertEqual(user.pk, response.context['flickr_user'].pk)

        self.assertIn('photo_list', response.context)
        self.assertEqual(len(response.context['photo_list']), 2)
        # ie, only user's photos.
        self.assertIn(users_photos[0], response.context['photo_list'])
        self.assertIn(users_photos[1], response.context['photo_list'])

    def test_user_detail_privacy(self):
        "It doesn't show private photos."
        user = factories.UserFactory()
        public_photo = factories.PhotoFactory(user=user)
        private_photo = factories.PhotoFactory(user=user, is_private=True)

        response = self.client.get(reverse('flickr:user_detail',
                                                kwargs={'nsid': user.nsid}))
        self.assertIn('photo_list', response.context)
        self.assertEqual(len(response.context['photo_list']), 1)
        self.assertIn(public_photo, response.context['photo_list'])

