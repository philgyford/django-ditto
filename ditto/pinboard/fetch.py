# coding: utf-8
import datetime
import json
import pytz
import requests
import urllib

from .models import Account, Bookmark
from ..core.utils import datetime_now


PINBOARD_API_ENDPOINT = "https://api.pinboard.in/v1/"
PINBOARD_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
PINBOARD_ALTERNATE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
PINBOARD_DATE_FORMAT = "%Y-%m-%d"


class FetchError(Exception):
    pass


class BookmarksFetcher(object):
    """The parent class containing common methods.
    Use one of the child classes to fetch a particular set of Bookmarks.
    """

    def fetch(self):
        raise FetchError('Call a child class like AllBookmarksFetcher or RecentBookmarksFetcher')


    def _fetch(self, fetch_type, params={}, username=None):
        """The main method for making all types of Bookmark requests, and
        saving the data.

        Keyword arguments:
        fetch_type -- 'all', 'date', 'recent' or 'url'.
        params -- Any params specific to the type (eg, url='http://foo.com')
                    These will be used directly with the Pinboard API.
        username -- the username of the one Account to fetch (or None for all).
        """
        # Each element will be a dict, like:
        # {'account':'philgyford', 'success':True, 'fetched':12}
        result = []

        accounts = self._get_accounts(username)

        for account in accounts:
            fetch_time = datetime_now()

            response = self._send_request(fetch_type, params, account)

            if response['success']:
                # Tidy the raw data:
                bookmarks_data = self._parse_response(
                                                fetch_type, response['json'])
                # Create/update in DB:
                self._save_bookmarks(
                                account=account,
                                bookmarks_data=bookmarks_data,
                                fetch_time=fetch_time)
                response['fetched'] = len(bookmarks_data)
                # Don't need to pass this around any more:
                del(response['json'])
            else:
                response['fetched'] = 0

            response['account'] = account.username
            result.append(response)

        return result

    def _get_accounts(self, username):
        """Get all or one active accounts.
        username is None or a username.
        Raises FetchError if we find that none of the required accounts are
        marked as is_active.
        """
        if username is None:
            accounts = Account.objects.filter(is_active=True)
            if len(accounts) == 0:
                raise FetchError("No active accounts were found to fetch.")
        else:
            account = Account.objects.get(username=username)
            if account.is_active:
                accounts = [account]
            else:
                raise FetchError("The account %s is curently marked as inactive." % username)
        return accounts

    def _send_request(self, fetch_type, params, account):
        """Sends a request to the Pinboard API, returns the raw response.

        Returns a dict with a 'success' element: True or False.
        If False, will have a 'messages' element, a list.
        If True, will have a 'json' element with the fetched data in.

        Keyword arguments:
        fetch_type -- 'all', 'date', 'recent' or 'url'.
        params -- Any params needed for this type. eg 'dt':datetime.
        Account -- The account to fetch from.
        """

        url_parts = ['posts']
        if fetch_type in ['date', 'url']:
            url_parts.append('get')
        elif fetch_type == 'recent':
            url_parts.append('recent')
        elif fetch_type == 'all':
            url_parts.append('all')

        url = "{}{}".format(PINBOARD_API_ENDPOINT, "/".join(url_parts))

        params['format'] = "json"
        params['auth_token'] = account.api_token
        query_string = urllib.parse.urlencode(params)

        final_url = "{}?{}".format(url, query_string)

        error_message = ''

        try:
            response = requests.get(final_url)
        except requests.exceptions.ConnectionError as e:
            error_message = "Can't connect to domain."
        except requests.exceptions.Timeout as e:
            error_message = "Connection timed out."
        except requests.exceptions.TooManyRedirects as e:
            error_message = "Too many redirects."
        except requests.exceptions.RequestException as e:
            error_message = "Something went wrong with the request."

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # 4xx or 5xx errors:
            error_message = "HTTP Error: %s" % response.status_code
        except NameError:
            if error_message == '':
                error_message = "Something unusual went wrong."

        if error_message:
            return {'account': account.username, 'success': False,
                                                'messages': [error_message,]}
        else:
            return {'account': account.username, 'success': True,
                                                        'json': response.text}


    def _parse_response(self, fetch_type, json_text):
        """Takes the JSON response for a Bookmark from the API and turns it
        into something more pythony.
        Returns a list of bookmark data.

        Keyword arguments:
        fetch_type -- 'all', 'date', 'recent' or 'url'.
        json_text -- The raw JSON returned from the API.
        """

        response = json.loads(json_text)

        # The JSON has different formats depending on what we fetched:
        if fetch_type == 'all':
            posts = response
        else:
            posts = response['posts']

        for bookmark in posts:
            # Before we do anything to it, we give the bookmark a 'json'
            # element with its original state in:
            bookmark['json'] = json.dumps(bookmark)
            # Time string to object:
            bookmark['time'] = datetime.datetime.strptime(
                                        bookmark['time'], '%Y-%m-%dT%H:%M:%SZ'
                                    ).replace(tzinfo=pytz.utc)
            # 'yes'/'no' to booleans:
            bookmark['shared'] = True if bookmark['shared'] == 'yes' else False
            bookmark['toread'] = True if bookmark['toread'] == 'yes' else False
            # String into an array of strings:
            bookmark['tags'] = bookmark['tags'].split()

        return posts

    def _save_bookmarks(self, account, bookmarks_data, fetch_time):
        """Takes the raw JSON response from the API, creates or updates the
        Bookmark objects.

        Keyword arguments:
        account -- The Account object to add these bookmarks for.
        bookmarks_data -- A list, each one data to create a single Bookmark.
        fetch_time -- The UTC time at which these bookmarks were fetched.
        """
        for bookmark in bookmarks_data:
            self._save_bookmark(bookmark, fetch_time, account)

    def _save_bookmark(self, bookmark, fetch_time, account):
        """Takes data for a single bookmark from the API response and creates
        or updates the Bookmark object.

        Keyword arguments:
        bookmark_data -- A list, each one data to create a single Bookmark.
        fetch_time -- The UTC time at which these bookmarks were fetched.
        account -- The Account object to add these bookmarks for.
        """

        bookmark_obj, created = Bookmark.objects.update_or_create(
            account=account,
            url=bookmark['href'],
            defaults={
                'title': bookmark['description'],
                'is_private': not bookmark['shared'],
                'raw': bookmark['json'],
                'description': bookmark['extended'],
                'to_read': bookmark['toread'],
                'fetch_time': fetch_time,
                'post_time': bookmark['time'],
            }
        )

        bookmark_obj.tags.set(*bookmark['tags'])


class AllBookmarksFetcher(BookmarksFetcher):

    def fetch(self, username=None):
        """Fetches all of the Bookmarks for all or one Accounts.
        Creates/updates the Bookmark objects.

        Keyword arguments:
        username -- the username of the one Account to fetch (or None for all).
        """
        return self._fetch(fetch_type='all', username=username)


class DateBookmarksFetcher(BookmarksFetcher):

    def fetch(self, post_date, username=None):
        """Fetches Bookmarks for all or one Accounts on a particular day.
        Creates/updates the Bookmark objects.

        Keyword arguments:
        post_date -- date to fetch in a "YYYY-MM-DD" format string.
        username -- the username of the one Account to fetch (or None for all).

        Raises:
        FetchError if the date format is invalid.
        """
        try:
            dt = datetime.datetime.strptime(post_date, '%Y-%m-%d')
        except ValueError:
            raise FetchError("Invalid date format ('%s')" % post_date)
        else:
            return self._fetch(
                    fetch_type='date', params={'dt': dt}, username=username)


class RecentBookmarksFetcher(BookmarksFetcher):

    def fetch(self, num=10, username=None):
        """Fetches the most recent Bookmarks for all or one Accounts.
        Creates/updates the Bookmark objects.

        Keyword arguments:
        num -- the number of most recent Bookmarks to fetch.
        username -- the username of the one Account to fetch (or None for all).
        """
        return self._fetch(
            fetch_type='recent', params={'count': int(num)}, username=username)


class UrlBookmarksFetcher(BookmarksFetcher):

    def fetch(self, url, username=None):
        """Fetches a single Bookmark (by URL) for all or one Accounts.
        Creates/updates the Bookmark objects.

        Keyword arguments:
        url -- the URL of the Bookmark to fetch.
        username -- the username of the one Account to fetch (or None for all).
        """
        return self._fetch(
                    fetch_type='url', params={'url': url}, username=username)


