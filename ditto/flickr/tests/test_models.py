import datetime
import pytz
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


class PhotoTestCase(TestCase):

    def test_ordering(self):
        "Latest photo should come first by default."
        photo_1 = PhotoFactory(title='Earliest',
            taken_time=datetime.datetime.strptime(
                '2016-04-07 12:00:00', '%Y-%m-%d %H:%M:%S'
            ).replace(tzinfo=pytz.utc))
        photo_2 = PhotoFactory(title='Latest',
            taken_time=datetime.datetime.strptime(
                '2016-04-08 12:00:00', '%Y-%m-%d %H:%M:%S'
            ).replace(tzinfo=pytz.utc))
        photos = Photo.objects.all()
        self.assertEqual(photos[0].title, 'Latest')
        self.assertEqual(photos[1].title, 'Earliest')

    def test_summary(self):
        "Summary should be made correctly on save."
        photo = PhotoFactory(
                description="Some <b>test HTML</b>.\n\nAnd another paragraph.")
        self.assertEqual(photo.summary, "Some test HTML. And another paragraph.")
        
        

