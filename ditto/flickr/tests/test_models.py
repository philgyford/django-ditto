import datetime
import pytz

from django.db import IntegrityError
from django.test import TestCase

from ..factories import AccountFactory, PhotoFactory, UserFactory
from ..models import Account, Photo, User


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


class PhotoTestCase(TestCase):

    def test_str(self):
        "Has the correct string represntation"
        photo = PhotoFactory(title='My test photo')
        self.assertEqual(photo.__str__(), 'My test photo')

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

    def test_summary_creation(self):
        "Summary should be made correctly on save."
        photo = PhotoFactory(
                description="Some <b>test HTML</b>.\n\nAnd another paragraph.")
        self.assertEqual(photo.summary, "Some test HTML. And another paragraph.")

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

