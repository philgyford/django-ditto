from django.core.urlresolvers import reverse
from django.test import TestCase

from ..factories import AccountFactory, PhotoFactory, TagFactory,\
        TaggedPhotoFactory, UserFactory


class ViewTests(TestCase):

    # HOME

    def test_home_templates(self):
        "The Flickr home page uses the correct templates"
        response = self.client.get(reverse('flickr:index'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'flickr/index.html')
        self.assertTemplateUsed(response, 'flickr/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_home_context(self):
        "The Flickr home page sends the correct data to templates"
        accounts = AccountFactory.create_batch(3)
        photos_1 = PhotoFactory.create_batch(2, user=accounts[0].user)
        photos_2 = PhotoFactory.create_batch(2, user=accounts[1].user)
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
        user_1 = UserFactory()
        user_2 = UserFactory()
        account_1 = AccountFactory(user=user_1)
        account_2 = AccountFactory(user=user_2)

        public_photo_1 = PhotoFactory(user=user_1)
        private_photo_1 = PhotoFactory(user=user_1, is_private=True)
        public_photo_2 = PhotoFactory(user=user_2)
        private_photo_2 = PhotoFactory(user=user_2, is_private=True)

        response = self.client.get(reverse('flickr:index'))
        photos = response.context['photo_list']
        self.assertEqual(len(photos), 2)
        self.assertEqual(photos[0].pk, public_photo_1.pk)
        self.assertEqual(photos[1].pk, public_photo_2.pk)

    # USER DETAIL

    def test_user_detail_templates(self):
        "Uses the correct templates"
        account = AccountFactory()
        response = self.client.get(reverse('flickr:user_detail',
                                        kwargs={'nsid': account.user.nsid}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'flickr/user_detail.html')
        self.assertTemplateUsed(response, 'flickr/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_user_detail_context_no_account(self):
        "Sends correct data to templates for a User with no Account."
        user = UserFactory()
        users_photos = PhotoFactory.create_batch(2, user=user)
        other_photos = PhotoFactory.create_batch(2)

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
        user = UserFactory()
        account = AccountFactory(user=user)
        users_photos = PhotoFactory.create_batch(2, user=user)
        other_photos = PhotoFactory.create_batch(2)

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
        user = UserFactory()
        public_photo = PhotoFactory(user=user)
        private_photo = PhotoFactory(user=user, is_private=True)

        response = self.client.get(reverse('flickr:user_detail',
                                                kwargs={'nsid': user.nsid}))
        self.assertIn('photo_list', response.context)
        self.assertEqual(len(response.context['photo_list']), 1)
        self.assertIn(public_photo, response.context['photo_list'])

    # PHOTO DETAIL

    def test_photo_detail_templates(self):
        "Uses the correct templates"
        account = AccountFactory()
        photos = PhotoFactory.create_batch(3, user=account.user)
        response = self.client.get(reverse('flickr:photo_detail',
                                    kwargs={'nsid': account.user.nsid,
                                            'flickr_id': photos[1].flickr_id}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'flickr/photo_detail.html')
        self.assertTemplateUsed(response, 'flickr/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_photo_detail_context(self):
        "Sends the correct data to templates"
        account = AccountFactory()
        photos = PhotoFactory.create_batch(3, user=account.user)
        response = self.client.get(reverse('flickr:photo_detail',
                                    kwargs={'nsid': account.user.nsid,
                                            'flickr_id': photos[1].flickr_id}))
        self.assertIn('account', response.context)
        self.assertEqual(account.pk, response.context['account'].pk)
        self.assertIn('flickr_user', response.context)
        self.assertEqual(account.user.pk, response.context['flickr_user'].pk)
        self.assertIn('photo', response.context)
        self.assertEqual(photos[1].pk, response.context['photo'].pk)

    def test_photo_detail_context_no_account(self):
        "Sends correct data to templates when showing a photo with no account"
        user = UserFactory()
        photos = PhotoFactory.create_batch(3, user=user)
        response = self.client.get(reverse('flickr:photo_detail',
                                    kwargs={'nsid': user.nsid,
                                            'flickr_id': photos[1].flickr_id}))
        self.assertIn('account', response.context)
        self.assertIsNone(response.context['account'])
        self.assertIn('flickr_user', response.context)
        self.assertEqual(user.pk, response.context['flickr_user'].pk)
        self.assertIn('photo', response.context)
        self.assertEqual(photos[1].pk, response.context['photo'].pk)

    def test_photo_detail_privacy(self):
        "It does not show private Photos"
        user = UserFactory()
        photo = PhotoFactory(is_private=True)
        response = self.client.get(reverse('flickr:photo_detail',
                                    kwargs={'nsid': user.nsid,
                                            'flickr_id': photo.flickr_id}))
        self.assertEqual(response.status_code, 404)

class TagViewTests(TestCase):
    """Have a bit more set up than the other tests, so may as well share it."""

    def setUp(self):
        """
        Creates two photos sharing three tags:
        1 has 'fish' and 'carp' tags.
        2 has 'fish' and 'cod' tags.
        """
        self.carp_photo = PhotoFactory(title='Carp')
        self.cod_photo = PhotoFactory(title='Cod')
        fish_tag = TagFactory(slug='fish', name='Fish')
        carp_tag = TagFactory(slug='carp', name='Carp')
        cod_tag = TagFactory(slug='cod', name='Cod')
        taggedphoto_1 = TaggedPhotoFactory(
                                content_object=self.carp_photo, tag=fish_tag)
        taggedphoto_2 = TaggedPhotoFactory(
                                content_object=self.carp_photo, tag=carp_tag)
        taggedphoto_3 = TaggedPhotoFactory(
                                content_object=self.cod_photo, tag=fish_tag)
        taggedphoto_4 = TaggedPhotoFactory(
                                content_object=self.cod_photo, tag=cod_tag)

    def createDogPhoto(self):
        "Creates a photo tagged with 'dog' and 'mammal'."
        self.dog_photo = PhotoFactory(title='Dog')
        mammal_tag = TagFactory(slug='mammal')
        dog_tag = TagFactory(slug='dog')
        taggedphoto_5 = TaggedPhotoFactory(
                                content_object=self.dog_photo, tag=mammal_tag)
        taggedphoto_6 = TaggedPhotoFactory(
                                content_object=self.dog_photo, tag=dog_tag)

    # TAG LIST

    def test_tag_list_templates(self):
        "Uses the correct templates"
        # Shouldn't need any photos to exist.
        response = self.client.get(reverse('flickr:tag_list'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'flickr/tag_list.html')
        self.assertTemplateUsed(response, 'flickr/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_tag_list_context(self):
        "Sends the correct data to templates"
        response = self.client.get(reverse('flickr:tag_list'))
        self.assertIn('tag_list', response.context)
        self.assertEqual(len(response.context['tag_list']), 3)

    def test_tag_list_privacy(self):
        "Should only show tags from public Photos"
        self.carp_photo.is_private = True
        self.carp_photo.save()
        response = self.client.get(reverse('flickr:tag_list'))
        self.assertIn('tag_list', response.context)
        self.assertEqual(len(response.context['tag_list']), 2)

    # TAG DETAIL

    def test_tag_detail_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('flickr:tag_detail',
                                                    kwargs={'slug': 'fish'}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'flickr/tag_detail.html')
        self.assertTemplateUsed(response, 'flickr/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_tag_detail_context(self):
        "Sends the correct data to the templates"
        accounts = AccountFactory.create_batch(2)
        # The 'fish' tag page shouldn't include this dog photo:
        self.createDogPhoto()
        response = self.client.get(reverse('flickr:tag_detail',
                                                    kwargs={'slug': 'fish'}))

        self.assertIn('account_list', response.context)
        self.assertEqual(
            [account.pk for account in response.context['account_list']],
            [1,2]
        )
        self.assertIn('tag', response.context)
        self.assertEqual(response.context['tag'].slug, 'fish')
        self.assertIn('photo_list', response.context)
        self.assertEqual(len(response.context['photo_list']), 2)
        self.assertEqual(response.context['photo_list'][0].title, 'Carp')
        self.assertEqual(response.context['photo_list'][1].title, 'Cod')

    def test_tag_detail_privacy(self):
        "Does not display private Photos"
        self.carp_photo.is_private = True
        self.carp_photo.save()
        response = self.client.get(reverse('flickr:tag_detail',
                                                    kwargs={'slug': 'carp'}))
        self.assertEquals(response.status_code, 404)

    def test_tag_detail_fails(self):
        "Returns a 404 if a non-existent tag's page is requested"
        response = self.client.get(reverse('flickr:tag_detail',
                                                    kwargs={'slug': 'bob'}))
        self.assertEquals(response.status_code, 404)

    ## USER TAG DETAIL

    def test_user_tag_detail_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('flickr:user_tag_detail',
            kwargs={'nsid': self.carp_photo.user.nsid, 'tag_slug': 'fish'}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'flickr/user_tag_detail.html')
        self.assertTemplateUsed(response, 'flickr/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_user_tag_detail_context(self):
        "Sends the correct data to templates"
        self.createDogPhoto()

        # Ensure the cod, carp and dog photos are all owned by the same user.
        # Only the carp and cod pics should show up on the user's 'fish' page.
        self.cod_photo.user = self.carp_photo.user
        self.cod_photo.save()
        self.dog_photo.user = self.carp_photo.user
        self.dog_photo.save()

        response = self.client.get(reverse('flickr:user_tag_detail',
                kwargs={'nsid': self.carp_photo.user.nsid, 'tag_slug': 'fish'}))

        self.assertIn('tag', response.context)
        self.assertEqual(response.context['tag'].name, 'Fish')
        self.assertIn('photo_list', response.context)
        self.assertEqual(len(response.context['photo_list']), 2)
        self.assertEqual(
            [photo.pk for photo in response.context['photo_list']],
            [1,2]
        )

    def test_user_tag_detail_privacy(self):
        "Does not display private photos"
        self.carp_photo.is_private = True
        self.carp_photo.save()
        response = self.client.get(reverse('flickr:user_tag_detail',
            kwargs={'nsid': self.carp_photo.user.nsid, 'tag_slug': 'carp'}))
        self.assertEquals(response.status_code, 404)

    def test_user_tag_detail_fails_1(self):
        "Returns a 404 if a non-existent user is requested"
        response = self.client.get(reverse('flickr:user_tag_detail',
                    kwargs={'nsid': '99999999999@N99', 'tag_slug': 'fish'}))
        self.assertEquals(response.status_code, 404)

    def test_user_tag_detail_fails_2(self):
        "Returns a 404 if a non-existent tag is requested"
        response = self.client.get(reverse('flickr:user_tag_detail',
            kwargs={'nsid': self.carp_photo.user.nsid, 'tag_slug': 'mammal'}))
        self.assertEquals(response.status_code, 404)

