import calendar
from datetime import datetime, timedelta
import json
import pytz
import requests
import time
import urllib

from ditto import TITLE, VERSION
from .models import Account, Album, Artist, Scrobble, Track
from .utils import slugify_name
from ..core.utils import datetime_now


LASTFM_API_ENDPOINT = 'http://ws.audioscrobbler.com/2.0/'


class FetchError(Exception):
    pass


class ScrobblesFetcher(object):
    """
    Fetches scrobbles from the API for one Account.

    Use like one of:
        fetcher = ScrobblesFetcher(account)

    And then one of these ('recent' is the default):
        results = fetcher.fetch(fetch_type='recent')
        results = fetcher.fetch(fetch_type='all')
        results = fetcher.fetch(fetch_type='days', days=3)
    """
    # How many scrobbles do we fetch per page of results?
    items_per_page = 200

    def __init__(self, account):

        # Will be an Account object, passed into init()
        self.account = None

        # We'll set this to a datetime if we're fetching scrobbles since x.
        self.min_datetime = None

        self.page_number = 1

        self.total_pages = 1

        self.results_count = 0

        # What we'll return:
        self.return_value = {'fetched': 0}

        if isinstance(account, Account):
            self.return_value['account'] = str(account)
        else:
            raise ValueError("An Account object is required")

        if account.has_credentials():
            self.account = account
        else:
            self.return_value['success'] = False
            self.return_value['messages'] = ['Account has no API credentials']

    def fetch(self, fetch_type='recent', days=None):
        """
        Fetch and save scrobbles.

        Keyword arguments:
        fetch_type -- 'all', 'days' or 'recent'. The latter will fetch
                      scrobbles since the most recent Scrobble we already have.
        days -- if fetch_type is 'days', this should be an integer.

        Returns a dict like:
            {'success': True, 'account': 'gyford', 'fetched': 47,}
        Or:
            {'success': False, 'account': 'gyford', 'messages': ['Oops..',],}
        """

        if self.account and self.account.is_active == False:
            self.return_value['success'] = False
            self.return_value['messages'] = [
                    'The Account %s is currently marked as inactive.' %\
                                                        self.account.username]
            return self.return_value

        valid_fetch_types = ['all', 'days', 'recent']
        if fetch_type not in valid_fetch_types:
            raise ValueError('fetch_type should be one of %s' %\
                                                ', '.join(valid_fetch_types))

        if fetch_type == 'days':
            try:
                test = days + 1
            except TypeError:
                raise ValueError('days argument should be an integer')

            self.min_datetime = datetime_now() - timedelta(days=days)

        elif fetch_type == 'recent':
            try:
                scrobble = Scrobble.objects.latest('post_time')
                self.min_datetime = scrobble.post_time
            except Scrobble.DoesNotExist:
                pass

        self._fetch_pages()

        if self._not_failed():
            self.return_value['success'] = True
            self.return_value['fetched'] = self.results_count

        return self.return_value

    def _fetch_pages(self):
        while self.page_number <= self.total_pages and self._not_failed():
            self._fetch_page()
            self.page_number += 1
            time.sleep(0.5)

    def _fetch_page(self):
        """
        Fetch a single page of results.
        Uses the value of self.page_number.
        """
        fetch_time = datetime_now()

        try:
            results = self._send_request()
        except FetchError as e:
            self.return_value['success'] = False
            self.return_value['messages'] = [str(e)]
            return

        for scrobble in results:
            if 'date' in scrobble:
                # Don't save nowplaying scrobbles, that have no 'date'.
                self._save_scrobble(scrobble, fetch_time)
                self.results_count += 1

        return

    def _not_failed(self):
        """Has everything gone smoothly so far? ie, no failure registered?"""
        if 'success' not in self.return_value or self.return_value['success'] == True:
            return True
        else:
            return False

    def _api_method(self):
        "The name of the API method."
        return 'user.getrecenttracks'

    def _api_args(self):
        "Returns a dict of args for the API call."
        args = {
            'user':     self.account.username,
            'api_key':  self.account.api_key,
            'format':   'json',
            'method':   self._api_method(),
            'page':     self.page_number,
            'limit':    self.items_per_page,
        }

        if self.min_datetime:
            # Turn our datetime object into a unix timestamp:
            args['from'] = calendar.timegm(self.min_datetime.timetuple())

        return args

    def _send_request(self):
        """
        Send a request to the Last.fm API.

        Raises FetchError if something goes wrong.
        Returns a list of results if all goes well.
        """
        query_string = urllib.parse.urlencode(self._api_args())

        url = "{}?{}".format(LASTFM_API_ENDPOINT, query_string)

        try:
            response = requests.get(url,
                        headers={'User-Agent': 'Mozilla/5.0 (%s v%s)' % (
                                                            TITLE, VERSION)})
            response.raise_for_status() # Raises an exception on HTTP error.
        except requests.exceptions.RequestException as e:
            raise FetchError(
                    "Error when fetching Scrobbles (page %s): %s" % \
                                                    (self.page_number, str(e)))

        results = json.loads(response.text)

        if 'error' in results:
            raise FetchError(
                    "Error %s when fetching Scrobbles (page %s): %s" % \
                    (results['error'], self.page_number, results['message'])
                )

        # Set total number of pages first time round:
        attr = results['recenttracks']['@attr']
        if self.page_number == 1 and 'totalPages' in attr:
            self.total_pages = int(attr['totalPages'])

        return results['recenttracks']['track']

    def _save_scrobble(self, scrobble, fetch_time):
        """
        Saves/updates a scrobble.

        Arguments:
        scrobble -- A dict of data from the Last.fm API.
        fetch_time -- Datetime of when the data was fetched.
        """
        artist_slug, track_slug = self._get_slugs(scrobble['url'])

        artist, created = Artist.objects.update_or_create(
            slug=artist_slug.lower(),
            defaults={
                'name': scrobble['artist']['#text'],
                'original_slug': artist_slug,
                'mbid': scrobble['artist']['mbid'], # Might be "".
            }
        )

        track, created = Track.objects.update_or_create(
            slug=track_slug.lower(),
            artist=artist,
            defaults={
                'name': scrobble['name'],
                'original_slug': track_slug,
                'mbid': scrobble['mbid'], # Might be "".
            }
        )

        if scrobble['album']['#text'] == '':
            album = None
        else:
            # The API data doesn't provide a URL/slug for the album, so
            # we make our own:
            album_slug = slugify_name(scrobble['album']['#text'])

            album, created = Album.objects.update_or_create(
                slug=album_slug.lower(),
                artist=artist,
                defaults={
                    'name': scrobble['album']['#text'],
                    'original_slug': album_slug,
                    'mbid': scrobble['album']['mbid'], # Might be "".
                }
            )

        # Unixtime to datetime object:
        scrobble_time = datetime.utcfromtimestamp(
                            int(scrobble['date']['uts'])
                        ).replace(tzinfo=pytz.utc)

        scrobble_obj, created = Scrobble.objects.update_or_create(
            account=self.account,
            track=track,
            post_time=scrobble_time,
            defaults={
                'artist':       artist,
                'raw':          json.dumps(scrobble),
                'fetch_time':   fetch_time,
                'album':        album,
            }
        )

        return scrobble_obj

    def _get_slugs(self, scrobble_url):
        """
        Get the artist and track slugs from a scrobble's URL.
        The scrobble's URL is also the Track's URL.

        scrobble_url is like 'https://www.last.fm/music/Artist/_/Track'
        returns two strings, artist_slug and track_slug.
        """
        url = scrobble_url.rstrip('/')

        # Need to replace semicolons as urlparse() treats them (legitimately)
        # as alternatives to '&' as a query string separator, and so omits
        # anything after them.
        url = url.replace(';', '%3B')

        # www.last.fm/music/Artist/_/Track':
        url_path = urllib.parse.urlparse(url).path
        path_parts = url_path.split('/')

        artist_slug = path_parts[-3]  # 'Artist'
        track_slug = path_parts[-1]   # 'Track'

        # Put those naughty semicolons back in:
        artist_slug = artist_slug.replace('%3B', ';')
        track_slug = track_slug.replace('%3B', ';')

        return artist_slug, track_slug


class ScrobblesMultiAccountFetcher(object):
    """
    For fetching Scrobbles for ALL or ONE account(s).

    Usage example:
        results = ScrobblesMultiAccountFetcher().fetch(fetch_type='recent')

    Or:
        results = ScrobblesMultiAccountFetcher(username='bob').fetch(fetch_type='recent')

    results will be a list of dicts containing info about what was fetched (or
    went wrong) for each account.
    """

    # Will be a list of Account objects.
    accounts = []

    def __init__(self, username=None):
        """
        Gets all of the Accounts, or the single Account specified.

        username -- If username is set, we only use that Account, if active.
                    If it's not set, we use all active Accounts.
        """
        self.return_value = []

        if username is None:
            # Get all active Accounts.
            self.accounts = list(Account.objects.filter(is_active=True))
            if len(self.accounts) == 0:
                raise FetchError("No active Accounts were found to fetch.")
        else:
            # Find the Account associated with username.
            try:
                account = Account.objects.get(username=username)
            except Account.DoesNotExist:
                raise FetchError(
                    "There is no Account with the username '%s'" % username)
            if account.is_active == False:
                raise FetchError(
                    "The Account with the username '%s' is marked as inactive." % username)
            self.accounts = [account]

    def fetch(self, **kwargs):
        for account in self.accounts:
            self.return_value.append(
                ScrobblesFetcher(account).fetch(**kwargs)
            )

        return self.return_value

