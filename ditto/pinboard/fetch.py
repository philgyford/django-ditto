# coding: utf-8
import datetime
import json
import requests
import urllib

from .models import Account, Bookmark


PINBOARD_API_ENDPOINT = "https://api.pinboard.in/v1/"

class FetchBookmarks(object):

    def fetch_all(self, username=None):
        """Fetches all of the Bookmarks for all or one Accounts.
        Creates/updates the Bookmark objects.

        Keyword arguments:
        username -- the username of the one Account to fetch (or None for all).
        """
        return self._fetch(fetch_type='all', username=username)

    def fetch_date(self, post_date, username=None):
        """Fetches Bookmarks for all or one Accounts on a particular day.
        Creates/updates the Bookmark objects.

        Keyword arguments:
        post_date -- date to fetch in a "YYYY-MM-DD" format string.
        username -- the username of the one Account to fetch (or None for all).
        """
        try:
            dt = datetime.datetime.strptime(post_date, '%Y-%m-%d')
        except ValueError:
            return [{'success': False,
                        'message': "Invalid date format ('%s')" % post_date}]

        return self._fetch(
                    fetch_type='date', params={'dt': dt}, username=username)

    def fetch_recent(self, num=10, username=None):
        """Fetches the most recent Bookmarks for all or one Accounts.
        Creates/updates the Bookmark objects.

        Keyword arguments:
        num -- the number of most recent Bookmarks to fetch.
        username -- the username of the one Account to fetch (or None for all).
        """
        return self._fetch(
            fetch_type='recent', params={'count': int(num)}, username=username)

    def fetch_url(self, url, username=None):
        """Fetches a single Bookmark (by URL) for all or one Accounts.
        Creates/updates the Bookmark objects.

        Keyword arguments:
        url -- the URL of the Bookmark to fetch.
        username -- the username of the one Account to fetch (or None for all).
        """
        return self._fetch(
                    fetch_type='url', params={'url': url}, username=username)

    def _fetch(self, fetch_type, params={}, username=None):
        # if username
        #   check this is an Account.
        #   if so:
        #       accounts = [Account]
        #   else:
        #       return error
        # else:
        #   accounts = [all Accounts]
        #
        # For each Account(s):
        #   response = self.send_request(fetch_type, params, api_key)
        #   if successful:
        #       count = self.save_bookmarks(response)
        #       to_return.append({username: username, fetched: count})
        #   else:
        #       to_return.append({username: username, message: error})
        # return to_return

        result = []

        if username is not None:
            accounts = [Account.objects.get(username=username)]
        else:
            accounts = Account.objects.all()

        for account in accounts:
            response = self._send_request(fetch_type, params, account.api_token)
            if response['success']:
                bookmark_data = self._parse_response(response['json'])
                self._save_bookmarks(bookmark_data)
                response['fetched'] = len(bookmark_data)
                del(response['json'])
            else:
                response['fetched'] = 0

            response['account'] = account.username
            result.append(response)

        return result


    def _send_request(self, fetch_type, params, api_token):
        """Sends a request to the Pinboard API, returns the raw response.

        Returns a dict with a 'success' element: True or False.
        If False, will have a 'message' element.
        If True, will have a 'json' element with the fetched data in.

        Keyword arguments:
        fetch_type: 'all', 'date', 'recent' or 'url'.
        params: Any params needed for this type. eg 'dt':datetime.
        api_token: Pinboard API token for the account to fetch from.
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
        params['auth_token'] = api_token
        query_string = urllib.urlencode(params)

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
            return {'success': False, 'message': error_message}
        else:
            return {'success': True, 'json': response.text}


    def _save_bookmarks(self, bookmarks_data):
        """Takes the raw JSON response from the API, creates or updates the
        Bookmark objects.
        """
        pass

    def _parse_response(self, json_text):
        """Takes the JSON response for a Bookmark from the API and turns it
        into something more pythony.
        """
        json_response = json.loads(json_text)

        # TODO: Tidy data

        return json_response['posts']


