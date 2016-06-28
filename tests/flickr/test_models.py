import datetime
import os
import pytz
from unittest.mock import Mock, patch

from django.db import IntegrityError
from django.test import TestCase

from ditto.flickr import app_settings
from ditto.flickr.factories import AccountFactory, PhotoFactory,\
        PhotosetFactory, UserFactory
from ditto.flickr.models import Account, Photo, Photoset, User


class AccountTestCase(TestCase):

    def test_str(self):
        account = AccountFactory(user=UserFactory(realname='Terry'))
        self.assertEqual(str(account), 'Terry')
        account_2 = AccountFactory(user=None)
        self.assertEqual(str(account_2), str(account_2.pk))

    def test_ordering(self):
        account_1 = AccountFactory(user=UserFactory(realname='Terry'))
        account_2 = AccountFactory(user=UserFactory(realname='Bob'))
        accounts = Account.objects.all()
        self.assertEqual(accounts[0].user.realname, 'Bob')
        self.assertEqual(accounts[1].user.realname, 'Terry')

    def test_has_credentials(self):
        account_1 = AccountFactory(api_key='1234', api_secret='9876')
        self.assertTrue(account_1.has_credentials())
        account_2 = AccountFactory(api_key='', api_secret='')
        self.assertFalse(account_2.has_credentials())

    def test_get_absolute_url_no_user(self):
        account = AccountFactory(user=None)
        self.assertEqual(account.get_absolute_url(), '')

    def test_get_absolute_url_with_user(self):
        account = AccountFactory(user=UserFactory(nsid='1234567890@N01'))
        self.assertEqual(account.get_absolute_url(), '/flickr/1234567890@N01/')


class UserTestCase(TestCase):

    def test_name(self):
        user = UserFactory(realname='Terry')
        self.assertEqual(user.name, 'Terry')

    def test_ordering(self):
        user_1 = UserFactory(realname='Terry')
        user_2 = UserFactory(realname='Bob')
        users = User.objects.all()
        self.assertEqual(users[0].realname, 'Bob')
        self.assertEqual(users[1].realname, 'Terry')

    def test_users_with_accounts(self):
        user_1 = UserFactory(realname='Terry')
        user_2 = UserFactory(realname='Bob')
        account = AccountFactory(user=user_1)
        users = User.objects_with_accounts.all()
        self.assertEqual(users[0], user_1)

    def test_unique_nsid(self):
        "Ensures nsid is unique"
        user_1 = UserFactory(nsid='12345678901@N01')
        with self.assertRaises(IntegrityError):
            user_2 = UserFactory(nsid='12345678901@N01')

    def test_flickr_url(self):
        user = UserFactory()
        self.assertEqual(user.permalink, user.photos_url)

    def test_avatar_url(self):
        user = UserFactory(
                nsid='12345678901@N01', avatar__filename='12345678901N01.jpg')
        self.assertEqual(
            user.avatar_url,
                    'flickr/89/01/12345678901N01/avatars/12345678901N01.jpg')

    def test_avatar_url_missing(self):
        user = UserFactory(avatar=None)
        self.assertEqual(user.avatar_url, '/static/img/default_avatar.png')

    def test_original_icon_url(self):
        user = UserFactory(iconfarm=8, iconserver=7420, nsid='35034346050@N01')
        self.assertEqual(user.original_icon_url,
        'https://farm8.staticflickr.com/7420/buddyicons/35034346050@N01.jpg')

    def test_original_icon_url_default(self):
        user = UserFactory(iconserver=0)
        self.assertEqual(user.original_icon_url,
                                'https://www.flickr.com/images/buddyicon.gif')

    def test_get_absolute_url(self):
        user = UserFactory(nsid='1234567890@N01')
        self.assertEqual(user.get_absolute_url(), '/flickr/1234567890@N01/')


class PhotosetTestCase(TestCase):

    def test_str(self):
        "Has the correct string representation"
        photoset = PhotosetFactory(title='My test photoset')
        self.assertEqual(photoset.__str__(), 'My test photoset')

    def test_photoset_ordering(self):
        "Latest photoset should come first by default."
        photoset_1 = PhotosetFactory(title='Earliest',
            flickr_created_time=datetime.datetime.strptime(
                '2016-04-07 12:00:00', '%Y-%m-%d %H:%M:%S'
            ).replace(tzinfo=pytz.utc))
        photoset_2 = PhotosetFactory(title='Latest',
            flickr_created_time=datetime.datetime.strptime(
                '2016-04-08 12:00:00', '%Y-%m-%d %H:%M:%S'
            ).replace(tzinfo=pytz.utc))
        photosets = Photoset.objects.all()
        self.assertEqual(photosets[0].title, 'Latest')
        self.assertEqual(photosets[1].title, 'Earliest')

    def test_unique_flickr_id(self):
        "Ensures flickr_id is unique"
        photoset_1 = PhotosetFactory(flickr_id=123456)
        with self.assertRaises(IntegrityError):
            photoset_2 = PhotosetFactory(flickr_id=123456)

    def test_get_absolute_url(self):
        photoset = PhotosetFactory(user=UserFactory(nsid='1234567890@N01'),
                                    flickr_id='123')
        self.assertEqual(
            photoset.get_absolute_url(), '/flickr/1234567890@N01/albums/123/')

    def test_photo_ordering(self):
        "Should return photos in the correct order."
        photo_1 = PhotoFactory()
        photo_2 = PhotoFactory()
        photo_3 = PhotoFactory()
        photoset = PhotosetFactory()
        photoset.photos.add(photo_2, photo_1, photo_3)
        photos = photoset.photos.all()
        self.assertEqual(photos[0], photo_2)
        self.assertEqual(photos[1], photo_1)
        self.assertEqual(photos[2], photo_3)

    def test_public_photos(self):
        "public_photos() should only return public photos."
        public_photo = PhotoFactory(is_private=False)
        private_photo = PhotoFactory(is_private=True)
        photoset = PhotosetFactory()
        photoset.photos.add(public_photo, private_photo)
        self.assertEqual(len(photoset.public_photos()), 1)
        self.assertEqual(photoset.public_photos()[0], public_photo)

    def test_permalink(self):
        "Should point to the correct Flickr.com page"
        photoset = PhotosetFactory(user=UserFactory(nsid='1234567890@N01'),
                                    flickr_id='12345')
        self.assertEqual(photoset.permalink,
                'https://www.flickr.com/photos/1234567890@N01/albums/12345')


class PhotoTestCase(TestCase):

    def test_str(self):
        "Has the correct string representation"
        photo = PhotoFactory(title='My test photo')
        self.assertEqual(str(photo), 'My test photo')

    def test_ditto_item_name(self):
        photo = PhotoFactory()
        self.assertEqual(photo.ditto_item_name, 'flickr_photo')

    def test_get_absolute_url(self):
        photo = PhotoFactory(user=UserFactory(nsid='1234567890@N01'),
                            flickr_id=123456)
        self.assertEqual(photo.get_absolute_url(),
                '/flickr/1234567890@N01/123456/')

    def test_ordering(self):
        "Latest photo (uploaded) should come first by default."
        photo_1 = PhotoFactory(title='Earliest',
            post_time=datetime.datetime.strptime(
                '2016-04-07 12:00:00', '%Y-%m-%d %H:%M:%S'
            ).replace(tzinfo=pytz.utc))
        photo_2 = PhotoFactory(title='Latest',
            post_time=datetime.datetime.strptime(
                '2016-04-08 12:00:00', '%Y-%m-%d %H:%M:%S'
            ).replace(tzinfo=pytz.utc))
        photos = Photo.objects.all()
        self.assertEqual(photos[0].title, 'Latest')
        self.assertEqual(photos[1].title, 'Earliest')

    def test_unique_flickr_id(self):
        "Ensures flickr_id is unique"
        photo_1 = PhotoFactory(flickr_id=123456)
        with self.assertRaises(IntegrityError):
            photo_2 = PhotoFactory(flickr_id=123456)

    def test_account_exists(self):
        "If the photo is from an Account the account property should return it."
        user = UserFactory()
        account = AccountFactory(user=user)
        photo = PhotoFactory(user=user)
        self.assertEqual(photo.account, account)

    def test_account_none(self):
        "If photo isn't from an Account its account property should be None."
        photo = PhotoFactory(user=UserFactory())
        self.assertIsNone(photo.account)

    def test_safety_level_str(self):
        photo = PhotoFactory(safety_level=0)
        self.assertEqual(photo.safety_level_str, 'None')
        photo.safety_level=2
        self.assertEqual(photo.safety_level_str, 'Moderate')
        photo.safety_level=99
        self.assertIsNone(photo.safety_level_str)

    def test_location_str(self):
        photo = PhotoFactory(
                    locality_name='Abbey Dore',
                    county_name='',
                    region_name='England',
                    country_name='United Kingdom')
        self.assertEqual(photo.location_str,
                'Abbey Dore, England, United Kingdom')

    def test_has_exif_no(self):
        photo = PhotoFactory()
        self.assertFalse(photo.has_exif)

    def test_has_exif_yes_1(self):
        photo = PhotoFactory(exif_camera='foo')
        self.assertTrue(photo.has_exif)

    def test_has_exif_yes_2(self):
        photo = PhotoFactory(exif_flash='foo')
        self.assertTrue(photo.has_exif)

    def test_default_manager_recent(self):
        "The default manager includes public AND private photos."
        public_photo = PhotoFactory(is_private=False)
        private_photo = PhotoFactory(is_private=True)
        self.assertEqual(len(Photo.objects.all()), 2)

    def test_public_manager_recent(self):
        "The public manager ONLY includes public photos."
        public_photo = PhotoFactory(is_private=False)
        private_photo = PhotoFactory(is_private=True)
        photos = Photo.public_objects.all()
        self.assertEqual(len(photos), 1)
        self.assertEqual(photos[0], public_photo)

    def test_photos_manager(self):
        "Returns public AND private photos ONLY by an Account."
        user = UserFactory()
        account = AccountFactory(user=user)
        public_photo = PhotoFactory(is_private=False)
        public_photo_by_account = PhotoFactory(is_private=False, user=user)
        private_photo = PhotoFactory(is_private=True)
        private_photo_by_account = PhotoFactory(is_private=True, user=user)
        photos = Photo.photo_objects.all()
        self.assertEqual(len(photos), 2)
        self.assertIn(public_photo_by_account, photos)
        self.assertIn(private_photo_by_account, photos)

    def test_public_photos_manager(self):
        "Returns ONLY public photos, ONLY by an Account."
        user = UserFactory()
        account = AccountFactory(user=user)
        public_photo = PhotoFactory(is_private=False)
        public_photo_by_account = PhotoFactory(is_private=False, user=user)
        private_photo = PhotoFactory(is_private=True)
        private_photo_by_account = PhotoFactory(is_private=True, user=user)
        photos = Photo.public_photo_objects.all()
        self.assertEqual(len(photos), 1)
        self.assertEqual(photos[0], public_photo_by_account)

    #def test_favorites_manager(self):
    #def test_public_favorites_photos_manager(self):
    #def test_public_favorites_accounts_manager(self):

    def test_square_sizes(self):
        sizes = {
            'square_width': 75,
            'square_height': 75,
            'large_square_width': 150,
            'large_square_height': 150,
        }

        photo = PhotoFactory()
        for prop, size in sizes.items():
            self.assertEqual(getattr(photo, prop), size)


class PhotoUrlsTestCase(TestCase):
    "Parent for testing the URLs of photos and videos."

    def setUp(self):
        # Map size letters to property names:
        self.photo_sizes = {
            's': 'square_url',
            'q': 'large_square_url',
            't': 'thumbnail_url',
            'm': 'small_url',
            'n': 'small_320_url',
            'z': 'medium_640_url',
            'c': 'medium_800_url',
            'b': 'large_url',
            'h': 'large_1600_url',
            'k': 'large_2048_url',
        }

        # Map size names to property names:
        self.video_sizes = {
            'mobile':   'mobile_mp4_url',
            'site':     'site_mp4_url',
            'hd':       'hd_mp4_url',
            'orig':     'video_original_url',
        }


class PhotoUrlsRemoteTestCase(PhotoUrlsTestCase):
    "Testing the URLs of photos and videos when we're pointing at Flickr.com."

    def test_original_url(self):
        "By default, same as photo.remote_original_url."
        photo = PhotoFactory(farm=3, server='1234', flickr_id=4567,
                  secret='9876', original_secret='7777', original_format='gif')
        self.assertEqual(photo.original_url,
            'https://farm3.static.flickr.com/1234/4567_7777_o.gif')

    def test_remote_original_url(self):
        "By default, same as photo.original_url."
        photo = PhotoFactory(farm=3, server='1234', flickr_id=4567,
                  secret='9876', original_secret='7777', original_format='gif')
        self.assertEqual(photo.remote_original_url,
            'https://farm3.static.flickr.com/1234/4567_7777_o.gif')

    def test_medium_url(self):
        "Has a different format to most other image sizes."
        photo = PhotoFactory(farm=3, server='1234', flickr_id=4567,
                                                                secret='9876')
        self.assertEqual(photo.medium_url,
            'https://farm3.static.flickr.com/1234/4567_9876.jpg')

    def test_image_urls(self):
        """Test all but the Original and Medium image URL properties."""
        photo = PhotoFactory(farm=3, server='1234', flickr_id=4567,
                                                                secret='9876')
        for size, prop in self.photo_sizes.items():
            self.assertEqual(getattr(photo, prop),
                'https://farm3.static.flickr.com/1234/4567_9876_%s.jpg' % size)

    def test_image_url_with_invalid_size(self):
        with self.assertRaises(AttributeError):
            self.photo.an_invalid_url

    def test_video_urls_video(self):
        "Videos should return the correct URLs from the video url properties."
        permalink = 'https://www.flickr.com/photos/philgyford/25743649964/'
        photo = PhotoFactory(media='video', permalink=permalink, secret=9876,
                                                        original_secret='7777')
        for size, prop in self.video_sizes.items():
            if size == 'orig':
                secret = 7777
            else:
                secret = 9876

            self.assertEqual(getattr(photo, prop),
                                '%splay/%s/%s/' % (permalink, size, secret))

    def test_video_urls_photo(self):
        "Photos should have None for all video URLs."
        photo = PhotoFactory(media='photo')

        for size, prop in self.video_sizes.items():
            self.assertIsNone(getattr(photo, prop))


class PhotoUrlsLocalTestCase(PhotoUrlsTestCase):
    "Testing the URLs of photos and videos when we're using local original files."

    def setUp(self):
        "Set the value of this setting that's used in ditto.flickr.models."
        super().setUp()
        self.default_use_local = app_settings.DITTO_FLICKR_USE_LOCAL_MEDIA
        app_settings.DITTO_FLICKR_USE_LOCAL_MEDIA = True

        self.photo = PhotoFactory(
                            user=UserFactory(nsid='123456@N01'),
                            taken_time=datetime.datetime.strptime(
                                '2015-08-14 12:00:00', '%Y-%m-%d %H:%M:%S'
                            ).replace(tzinfo=pytz.utc))

    def tearDown(self):
        app_settings.DITTO_FLICKR_USE_LOCAL_MEDIA = self.default_use_local

    def test_original_url(self):
        filename = os.path.basename(self.photo.original_file.name)
        self.assertEqual(self.photo.original_url,
                     'flickr/34/56/123456N01/photos/2015/08/14/%s' % filename)

    def test_remote_original_url(self):
        "Should still return remote URL when we're using local photos."
        photo = PhotoFactory(farm=3, server='1234', flickr_id=4567,
                  secret='9876', original_secret='7777', original_format='gif')
        self.assertEqual(photo.remote_original_url,
            'https://farm3.static.flickr.com/1234/4567_7777_o.gif')

    def test_medium_url(self):
        "Has a different format to most other image sizes."
        self.assertRegexpMatches(self.photo.medium_url,
            'CACHE/images/flickr/34/56/123456N01/photos/2015/08/14/example.[^\.]+\.jpg')

    def test_image_urls(self):
        """Test all but the Original and Medium image URL properties."""
        for size, prop in self.photo_sizes.items():
            self.assertRegexpMatches(getattr(self.photo, prop),
                'CACHE/images/flickr/34/56/123456N01/photos/2015/08/14/example.[^\.]+\.jpg')

    def test_image_url_with_invalid_size(self):
        with self.assertRaises(AttributeError):
            self.photo.an_invalid_url

    def test_video_urls_video(self):
        "Should currently return the remote URL for videos."
        permalink = 'https://www.flickr.com/photos/philgyford/25743649964/'
        photo = PhotoFactory(media='video', permalink=permalink, secret=9876,
                                                        original_secret='7777')
        for size, prop in self.video_sizes.items():
            if size == 'orig':
                secret = 7777
            else:
                secret = 9876

            self.assertEqual(getattr(photo, prop),
                                '%splay/%s/%s/' % (permalink, size, secret))

    def test_image_url_when_original_missing(self):
        "If we have no original file, we should use the 'missing' image."
        photo = PhotoFactory(original_file='')
        self.assertEqual(photo.small_url, '/static/img/original_missing.jpg')

    def test_broken_image(self):
        "We have an original file, but can't make a smaller version."
        generator = Mock(side_effect=Exception('Error'))
        # A minimal version of Photo.PHOTO_SIZES for our test:
        photo_sizes = {'small': {'generator': generator,},}
        with patch.dict('ditto.flickr.models.Photo.PHOTO_SIZES', photo_sizes):
            self.assertEqual(self.photo.small_url,
                             '/static/img/original_error.jpg')


class PhotoNextPrevTestCase(TestCase):

    def setUp(self):
        user = UserFactory()
        account = AccountFactory(user=user)
        self.photo_1 = PhotoFactory(user=user,
                                post_time=datetime.datetime.strptime(
                                    '2016-04-08 12:00:00', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.private_photo = PhotoFactory(user=user, is_private=True,
                                post_time=datetime.datetime.strptime(
                                    '2016-04-09 12:00:00', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        # Photo by a different user:
        user_2 = UserFactory()
        account_2 = AccountFactory(user=user_2)
        self.other_photo = PhotoFactory(user=user_2,
                                post_time=datetime.datetime.strptime(
                                    '2016-04-10 12:00:00', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.photo_2 = PhotoFactory(user=user,
                                    post_time=datetime.datetime.strptime(
                                    '2016-04-11 12:00:00', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))

    def test_next_public_by_post_time(self):
        self.assertEqual(self.photo_1.get_next_public_by_post_time(),
                        self.photo_2)

    def test_next_public_by_post_time_none(self):
        self.assertIsNone(self.photo_2.get_next_public_by_post_time())

    def test_previous_public_by_post_time(self):
        self.assertEqual(self.photo_2.get_previous_public_by_post_time(),
                        self.photo_1)

    def test_previous_public_by_post_time_none(self):
        self.assertIsNone(self.photo_1.get_previous_public_by_post_time())

    def test_next(self):
        self.assertEqual(self.photo_1.get_next(),self.photo_2)

    def test_next_none(self):
        self.assertIsNone(self.photo_2.get_next())

    def test_previous(self):
        self.assertEqual(self.photo_2.get_previous(), self.photo_1)

    def test_previous_none(self):
        self.assertIsNone(self.photo_1.get_previous())

