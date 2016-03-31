import calendar
import datetime
import json
import pytz

import flickrapi
from flickrapi.exceptions import FlickrError

from .models import Account, User

# CLASSES HERE:
#
# FetchError
#
# FlickrItemMixin
#   UserMixin               # Method for saving a User.
#       PhotoMixin          # Method for saving a Photo.
#
# Fetch
#   FetchUser               # Fetches and saves one Account's User.
#   FetchPhotos
#       FetchPhotosRecent   # Fetches and saves one Account's recent photos.
#
# FlickrFetcher
#   UserFetcher             # Fetches and saves one Account's User by URL.
#   RecentPhotosFetcher     # Fetches and saves Photos for one or all Accounts.
#
# Use a fetcher like:
#
#   fetcher = UserFetcher()
#   results = fetcher.fetch(url='https://www.flickr.com/photos/philgyford/')


class FetchError(Exception):
    pass


class FlickrItemMixin(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _api_datetime_to_datetime(self, api_time):
        """Change a text datetime from the API to a datetime with timezone.
        api_time is a string like "1956-01-01 00:00:00".
        """
        return datetime.datetime.strptime(
                        api_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)

    def _api_unixtime_to_datetime(self, api_time):
        """Change a text unixtime from the API to a datetime with timezone.
        api_time is a string or int like "1093459273".
        """
        return datetime.datetime.utcfromtimestamp(
                                        int(api_time)).replace(tzinfo=pytz.utc)


class UserMixin(FlickrItemMixin):
    "Provides a method for creating/updating a User using data from the API."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_user(self, user, fetch_time):
        """
        Keyword arguments:
        user -- A dict of the data about a user from the API's JSON.
        fetch_time -- A datetime.

        Returns the User object.
        """
        raw_json = json.dumps(user)

        defaults = {
            'fetch_time':   fetch_time,
            'raw':          raw_json,
            'nsid':         user['nsid'],
            'is_pro':       True if user['ispro'] == 1 else False,
            'iconserver':   user['iconserver'],
            'iconfarm':     user['iconfarm'],
            'username':     user['username']['_content'],
            'realname':     user['realname']['_content'],
            'location':     user['location']['_content'],
            'description':  user['description']['_content'],
            'photos_url':   user['photosurl']['_content'],
            'profile_url':  user['profileurl']['_content'],
            'photos_count': int(user['photos']['count']['_content']),
            'photos_first_date': self._api_unixtime_to_datetime(
                                user['photos']['firstdate']['_content']),
            'photos_first_date_taken': self._api_datetime_to_datetime(
                                user['photos']['firstdatetaken']['_content']),
        }

        if 'views' in user['photos']:
            # I think this might only be returned for the Account's own user.
            defaults['photos_views'] = \
                                    int(user['photos']['views']['_content'])

        user_obj, created = User.objects.update_or_create(
            nsid=user['nsid'], defaults=defaults
        )

        return user_obj


class PhotoMixin(UserMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_photo(self, photo, fetch_time):
        """Takes a dict of photo data from the API and creates or updates a
        Photo object and its associated User object.

        Keyword arguments:
        photo -- The photo data.
                 From the Flickr API. With extra fields:
                     'user': {'id': 4}
        fetch_time -- A datetime.

        Returns:
        The Photo object that was created or updated.
        """
        raw_json = json.dumps(photo)

        print(photo['id'])

        defaults = {
            'fetch_time':           fetch_time,
            'raw':                  raw_json,
            'user':                 user_id,
            'is_private':           (photo['ispublic'] == 0),
            'post_time':            photo['date_upload']
            
            'flickr_id':            photo['id'],
                
        }

        photo_obj, created = Photo.objects.update_or_create(
                flickr_id=photo['id'],
                defaults=defaults
            )

        return photo_obj


class Fetch(object):
    """Parent class for children that will call the Flickr API to fetch data.

    We call the fetch() method, which calls:
        _fetch_pages() which calls:
            _call_api() and puts data into self.results.
            If no data is returned then we're on final page and it calls:
                _save_results() which saves the objects.
    It keeps going on subsequent pages until we've got everything.

    Children must define their own methods for:
        _call_api()
        _save_results()
    """
    # Will be an Account object, passed into init()
    account = None

    # Will be the FlickrAPI object for calling the Flickr API.
    api = None

    # Will be the UTC datetime that we fetch the results.
    fetch_time = None

    # Will be the results fetched from the API via FlickrAPI.
    results = []

    # Will be a list of all the Users/Photos/etc created/updated:
    objects = []

    # What we'll return for each account:
    return_value = {}

    # When fetching Photos or Users this will be the total amount fetched.
    results_count = 0

    # The number of the page we last fetched (for things that have pages).
    page = 1

    # Will be set to the number of pages to fetch, when we get the first result.
    total_pages = 1

    def __init__(self, account):
        self.account = account

    def fetch(self):
        self._reset()

        if self.account.user:
            self.return_value['account'] = self.account.user.username
        elif self.account.pk:
            self.return_value['account'] = 'Account: %s' % str(self.account)
        else:
            self.return_value['account'] = 'Unsaved Account'

        if self.account.has_credentials():
            self.api = flickrapi.FlickrAPI(self.account.api_key,
                                self.account.api_secret, format='parsed-json')
            self._fetch_pages()
        else:
            self.return_value['success'] = False
            self.return_value['message'] = 'Account has no API credentials'

        self.return_value['fetched'] = self.results_count

        return self.return_value

    def _reset(self):
        self.fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        self.results = []
        self.objects = []
        self.return_value = {}
        self.results_count = 0

    def _fetch_pages(self):
        while self.page <= self.total_pages:
            try:
                self._call_api()
            except FetchError as e:
                self.return_value['success'] = False
                self.return_value['message'] = 'Error when calling API: %s' % e
            self.page += 1
        self._fetch_extra()
        # Got all the pages of results, data put into self.results:
        self._save_results()
        self.return_value['success'] = True
        return

    def _call_api(self):
        """Define in child classes.
        Should call self.api.a_function_name() and set self.results with the
        results.
        """
        raise FetchError("Children of the Fetch class should define their own _call_api() method.")

    def _fetch_extra(self):
        """Can be defined in child classes to fetch extra data to add to
        self.results before we save the data in the DB."""
        pass

    def _save_results(self):
        """Define in child classes.
        Should go through self._results() and, probably, call
        self.save_user() or self.save_photo() for each one.
        """
        raise FetchError("Children of the Fetch class should define their own _save_results() method.")


class FetchUser(UserMixin, Fetch):
    """Fetch and save info about a single user."""

    user_url = None

    def fetch(self, url=None):
        """
        url -- A Flickr URL owned by a user,
                eg 'https://www.flickr.com/photos/philgyford/8102921/'
        """
        self.user_url = url
        return super().fetch()

    def _call_api(self):
        "Get the User data from Flickr and save into self.results"

        # First, need to get the user's NSID using the URL we have:
        try:
            user = self.api.urls.lookupUser(url=self.user_url)
        except FlickrError as e:
            raise FetchError("Error when looking up user with URL '%s': %s" % (self.user_url, e))

        # Now we've got the NSID, get the user's info:
        try:
            info = self.api.people.getInfo(user_id=user['user']['id'])
        except FlickrError as e:
            raise FetchError("Error when getting info about User with id '%s': %s" % (user['user']['id'], e))

        # info has 'person' and 'stat' elements.
        self.results = [ info['person'] ]

    def _save_results(self):
        user_obj = self.save_user(self.results[0], self.fetch_time)
        self.objects.append(user_obj)
        self.return_value['user'] = {'name': user_obj.name}
        self.results_count = 1


class FetchPhotos(PhotoMixin, Fetch):

    # Will be the minimum date of upload/fave for Photos that we'll fetch.
    min_date = None

    # Will be 'new' or 'date':
    fetch_type = 'new'

    # 500 is the max the API allows.
    photos_per_page = 5

    # Will match Flickr IDs with our User IDs.
    # When we fetch a user's data, because we've just fetched their photo,
    # we add their IDs to this, so we don't fetch again this time.
    fetched_users = {}

    def __init__(self, *args, **kwargs):
        # Set default min_date:
        self.min_date = datetime.datetime.strptime('2000-01-01', '%Y-%m-%d')
        super().__init__(*args, **kwargs)

    def fetch(self, since='new'):
        """
        Keyword arguments:
        since -- Either 'new' (get the Photos since the last fetch) or a 
                'YYYY-MM-DD' date, which will get the photos uploaded/faved on
                or after that date.
        """
        if since == 'date':
            self.fetch_type = 'date'
            self.min_date = datetime.datetime.strptime(since, '%Y-%m-%d')
        else:
            self.fetch_type = 'new'

        return super().fetch()

    def _fetch_user(self, flickr_id):
        """
        Fetch, and save, a single user from the API, from their Flickr ID.
        Adds the User ID to self.fetched_users.
        """
        print("Fetching user %s" % flickr_id)
        try:
            user_info = self.api.people.getInfo(user_id=flickr_id)
        except FlickrError as e:
            raise FetchError("Error when getting info about User with id '%s': %s" % (flickr_id, e))

        user_obj = self.save_user(user_info['person'], self.fetch_time)
        self.fetched_users[flickr_id] = user_obj.id


class FetchPhotosRecent(FetchPhotos):
    """For fetching a list of recent photos by a single Account."""

    def _call_api(self):
        """Fetch one page of results, containing very basic info about the
        Photos."""
        # Turn our datetime object into a unix timestamp:
        min_unixtime = calendar.timegm(self.min_date.timetuple())

        try:
            results = self.api.people.getPhotos(
                                            user_id=self.account.user.nsid,
                                            min_upload_date=min_unixtime,
                                            per_page=self.photos_per_page,
                                            page=self.page
                                        )
        except FlickrError as e:
            raise FetchError("Error when fetching recent photos (page %s): %s" % (self.page, e))

        if self.page == 1 and 'photos' in results and 'pages' in esults['photos']:
            # First time, set the total_pages there are to fetch.
            self.total_pages == results['photos']['pages']

        # Add the list of photos' data from this page on to our total list:
        self.results += results['photos']['photo']

    def _fetch_extra(self):
        """Before saving we need to go through the big list of photos we've
        fetched, and fetch more detailed info to add to each photo's data.

        I've a feeling it's horrible to cycle through a list and amend each
        of its dicts in place, but...
        """
        for i, photo in enumerate(self.results):
            # TODO: getInfo()
            # TODO: getSizes() ?
            # TODO: geo_getLocation()
            # eg:
            # self.results[i]['sizes'] = blah

            #if self.fetched_users.get(photo['owner'], None) is None:
                # We haven't already fetched this user, so get it:
                #self._fetch_user(photo['owner'])

            # Add our ID of the photo's owner:
            # self.results[i]['user'] = {
            #                       'id': self.fetched_users[photo['owner']]}

            pass

    def _save_results(self):
        """Save all the data we've fetched about photos to the DB."""
        for photo in self.results:
            p = self.save_photo(photo, self.fetch_time)
            self.objects.append(p)



class FlickrFetcher(object):
    """Parent class for fetching things from Flickr.

    Use like:
        fetcher = ChildFlickrFetcher(username='philgyford')
        fetcher.fetch()

    Or, for all accounts:
        fetcher = ChildFlickrFetcher()
        fetcher.fetch()
    """

    def __init__(self, username=None):
        """Keyword arguments:
        username -- of the one Account to get, or None for all Accounts.

        Raises:
        FetchError if passed a username there is no Account for.
        """
        self._set_accounts(username)

        # Will be a list of dicts that we return detailing succes/failure
        # results, one dict per account we've fetched for. eg:
        # [ {'account': 'thescreename', 'success': True, 'fetched': 200} ]
        self.return_values = []

    def fetch(self, **kwargs):
        """Fetch data for one or more Accounts.

        Returns:
        A list of dicts, one dict per Account, containing data about
        success/failure.
        """
        for account in self.accounts:
            fetchObject = self._get_fetch_object(account)
            return_value = fetchObject.fetch(**kwargs)
            self._add_to_return_values(return_value)

        return self.return_values

    def _get_fetch_object(self, account):
        """Should be changed for each child class.
        Should return an instance of a child of Fetch().
        eg:
            return FetchThingy(account)

        Keyword arguments:
        account -- An Account object.
        """
        raise FetchError("Children of the FlickrFetcher class should define their own _get_fetch_object() method.")

    def _add_to_return_values(self, return_value):
        """Add return_value to the list in self.return_values."""
        self.return_values.append(return_value)

    def _set_accounts(self, username=None):
        """Sets self.accounts to all Accounts or just one.

        Keyword arguments:
        username -- of the one Account to get, or None for all Accounts.

        Raises:
        FetchError if passed a username there is no Account for, or if none
            of the requested account(s) are marked as is_active.
        """
        if username is None:
            accounts = Account.objects.filter(is_active=True)
            if (len(accounts) == 0):
                raise FetchError("No active Accounts were found to fetch.")
        else:
            try:
                accounts = [Account.objects.get(user__username=username)]
            except Account.DoesNotExist:
                raise FetchError("There is no Account in the database with a username of '%s'" % username)
            else:
                if accounts[0].is_active == False:
                    raise FetchError("The '%s' Account is marked as inactive." % username)

        self.accounts = accounts


class UserFetcher(FlickrFetcher):
    """Fetches data for a single Flickr user.
    Currently only accepts the URL of a page owned by that user. eg
    https://www.flickr.com/photos/philgyford/8102921/

    Usage:
        fetcher = UserFetcher()
        results = fetcher.fetch(url='https://www.flickr.com/philgyford')
    """
    def fetch(self, url=None):
        return super().fetch(url=url)

    def _get_fetch_object(self, account):
        return FetchUser(account)

    def _set_accounts(self, username=None):
        super()._set_accounts(username=username)
        if len(self.accounts) > 0:
            self.accounts = [self.accounts[0]]


#class PhotosFetcher(FlickrFetcher):

    #def fetch(self, ids=[]):
        #return super().fetch(ids=ids)

    #def _get_fetch_object(self, account):
        #return FetchPhotos(account)



class RecentPhotosFetcher(FlickrFetcher):
  
    def fetch(self, since='new'):
        return super().fetch(since=since)

    def _get_fetch_object(self, account):
        return FetchPhotosRecent(account)

