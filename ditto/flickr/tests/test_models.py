from django.test import TestCase

from ..factories import AccountFactory, UserFactory
from ..models import Account, User


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

