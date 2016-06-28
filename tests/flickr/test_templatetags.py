import datetime
import pytz

from django.test import TestCase

from freezegun import freeze_time

from ditto.core.templatetags.ditto_core import display_time
from ditto.core.utils import datetime_now
from ditto.flickr.templatetags import ditto_flickr
from ditto.flickr.factories import AccountFactory, PhotoFactory,\
        PhotosetFactory, UserFactory


class TemplatetagsRecentPhotosTestCase(TestCase):

    def setUp(self):
        user_1 = UserFactory(nsid='1234567890@N01')
        user_2 = UserFactory(nsid='9876543210@N01')
        account_1 = AccountFactory(user=user_1)
        account_2 = AccountFactory(user=user_2)
        self.photos_1 = PhotoFactory.create_batch(2, user=user_1)
        self.photos_2 = PhotoFactory.create_batch(3, user=user_2)
        self.private_photo = PhotoFactory(user=user_1, is_private=True)
        # For comparing with the results:
        self.public_pks = [p.pk for p in self.photos_1] + \
                                                [p.pk for p in self.photos_2]

    def test_recent_photos(self):
        "Returns recent photos from all public accounts"
        photos = ditto_flickr.recent_photos()
        self.assertEqual(5, len(photos))
        self.assertNotIn(self.private_photo.pk, self.public_pks)

    def test_recent_photos_account(self):
        "Returns recent photos from one account"
        photos = ditto_flickr.recent_photos(nsid='1234567890@N01')
        self.assertEqual(2, len(photos))

    def test_recent_photos_limit(self):
        photos = ditto_flickr.recent_photos(limit=4)
        self.assertEqual(4, len(photos))


class TemplatetagsPhotosetsTestCase(TestCase):

    def setUp(self):
        user_1 = UserFactory(nsid='1234567890@N01')
        user_2 = UserFactory(nsid='9876543210@N01')
        account_1 = AccountFactory(user=user_1)
        account_2 = AccountFactory(user=user_2)
        self.photosets_1 = PhotosetFactory.create_batch(2, user=user_1)
        self.photosets_2 = PhotosetFactory.create_batch(3, user=user_2)

    def test_photosets(self):
        "Returns photosets from all accounts"
        photosets = ditto_flickr.photosets()
        self.assertEqual(5, len(photosets))

    def test_photosets_account(self):
        "Returns photosets from one account"
        photosets = ditto_flickr.photosets(nsid='1234567890@N01')
        self.assertEqual(2, len(photosets))

    def test_photosets_limit(self):
        photosets = ditto_flickr.photosets(limit=4)
        self.assertEqual(4, len(photosets))


class TemplatetagsDayPhotosTestCase(TestCase):

    def setUp(self):
        user_1 = UserFactory(nsid='1234567890@N01')
        user_2 = UserFactory(nsid='9876543210@N01')
        account_1 = AccountFactory(user=user_1)
        account_2 = AccountFactory(user=user_2)
        self.photos_1 = PhotoFactory.create_batch(2, user=user_1)
        self.photos_2 = PhotoFactory.create_batch(3, user=user_2)

        post_time = datetime.datetime(2015, 3, 18, 12, 0, 0).replace(
                                                            tzinfo=pytz.utc)
        self.photos_1[0].post_time = post_time
        self.photos_1[0].save()
        self.photos_2[1].post_time = post_time + datetime.timedelta(hours=1)
        self.photos_2[1].save()

        self.private_photo = PhotoFactory(user=user_1, is_private=True,
                post_time = post_time)

    def test_day_photos(self):
        "Returns only public Photos from the date"
        photos = ditto_flickr.day_photos(datetime.date(2015, 3, 18))
        self.assertEqual(2, len(photos))
        self.assertEqual(photos[0].pk, self.photos_2[1].pk)
        self.assertEqual(photos[1].pk, self.photos_1[0].pk)

    def test_day_photos_one_account(self):
        "Returns only Photos from the day if it's the chosen account"
        photos = ditto_flickr.day_photos(
                            datetime.date(2015, 3, 18), nsid='1234567890@N01')
        self.assertEqual(1, len(photos))
        self.assertEqual(photos[0].pk, self.photos_1[0].pk)


class PhotoLicenseTestCase(TestCase):

    def test_license_0(self):
        self.assertEqual(
                        ditto_flickr.photo_license('0'), 'All Rights Reserved')

    def test_license_1(self):
        self.assertEqual(ditto_flickr.photo_license('1'),
            '<a href="https://creativecommons.org/licenses/by-nc-sa/2.0/" title="More about permissions">Attribution-NonCommercial-ShareAlike License</a>'
        )

    def test_license_99(self):
        self.assertEqual(ditto_flickr.photo_license('99'), '[missing]')


