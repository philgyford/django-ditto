# coding: utf-8
import responses

from django.test import TestCase

from .. import factories
from ..fetch import FetchTweets, FetchUsers
from ..models import Account, User


class FetchGetAccounts(TestCase):

    def test_returns_one_accont(self):
        pass

class FetchUsersTestCase(TestCase):

    api_url = 'https://api.twitter.com/1.1'

    api_fixture = 'ditto/twitter/fixtures/api/verify_credentials.json'

    def make_verify_credentials_body(self):
        "Makes the JSON response to a call to verify_credentials"
        json_file = open(self.api_fixture)
        json_data = json_file.read()
        json_file.close()
        return json_data

    def add_response(self, body, call, status=200):
        """Add a Twitter API response.

        Keyword arguments:
        body -- The JSON string representing the body of the response.
        call -- String, appended to self.api_url, eg
                    'account/verfiy_credentials'.
        status -- Int, HTTP response status
        """
        responses.add(
            responses.GET,
            '%s/%s.json' % (self.api_url, call),
            status=status,
            match_querystring=False,
            body=body,
            content_type='application/json; charset=utf-8'
        )

    @responses.activate
    def test_fetch_for_account_creates(self):
        "Saves and returns new user after successful API call"
        self.add_response(body=self.make_verify_credentials_body(),
                            call='account/verify_credentials')
        account = factories.AccountWithCredentialsFactory.build(id=4, user=None)

        result = FetchUsers().fetch_for_account(account=account)
        new_user = User.objects.get(twitter_id=12552)

        self.assertIsInstance(result, User)
        self.assertEqual(result.screen_name, 'philgyford')
        self.assertEqual(new_user.screen_name, 'philgyford')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)

    @responses.activate
    def test_fetch_for_account_updates(self):
        "Saves and returns updated existing user after successful API call"
        self.add_response(body=self.make_verify_credentials_body(),
                            call='account/verify_credentials')
        user = factories.UserFactory(twitter_id=12552, screen_name='bob')
        account = factories.AccountWithCredentialsFactory(user=user)

        result = FetchUsers().fetch_for_account(account=account)
        updated_user = User.objects.get(twitter_id=12552)

        self.assertIsInstance(result, User)
        self.assertEqual(result.screen_name, 'philgyford')
        self.assertEqual(updated_user.screen_name, 'philgyford')
        self.assertEqual(2, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)

    @responses.activate
    def test_fetch_for_account_fails(self):
        "Returns error message if API call fails"
        self.add_response(body='{"errors":[{"message":"Could not authenticate you","code":32}]}',
                            call='account/verify_credentials',
                            status=401)

        account = factories.AccountWithCredentialsFactory.build(user=None)
        result = FetchUsers().fetch_for_account(account=account)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)
        self.assertTrue('Could not authenticate you' in result)
