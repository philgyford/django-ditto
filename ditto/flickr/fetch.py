import calendar
import datetime
import json
import pytz

import flickrapi
from flickrapi.exceptions import FlickrError

from ..ditto.utils import truncate_string
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

    def _api_datetime_to_datetime(self, api_time, timezone_id='Etc/UTC'):
        """Change a text datetime from the API to a datetime with timezone.
        api_time is a string like "1956-01-01 00:00:00".
        timezone_id is a TZ timezone name like 'Africa/Accra'
        """
        tz = pytz.timezone(timezone_id)
        return datetime.datetime.strptime(
                            api_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz)

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
        photo -- The photo data, from several Flickr API calls.
                 Has keys:
                     'user_obj': User object for this photo's owner.
                     'info': Results of a photos.getInfo call.
                     'exif': Results of a photos.getExif call.
                     'sizes': Results of a photos.getSizes call.
        fetch_time -- A datetime.

        Returns:
        The Photo object that was created or updated.
        """

        # photo['urls'] = {'url': [{'type':'photopage', '_content':'http...'}]}
        permalink = next(url for url in photo['urls']['url'] if url['type'] == 'photopage')['_content']

        summary = truncate_string(photo['description']['_content'],
                strip_html=True, chars=255, truncate='…', at_word_boundary=True)

        defaults = {
            # DittoItemModel fields
            'title':                photo['info']['title']['_content'],
            'permalink':            permalink,
            'summary':              summary,
            'is_private':           (photo['info']['visibility']['ispublic'] == 0),
            'fetch_time':           fetch_time,
            'post_time':            self._api_unixtime_to_datetime(
                                            photo['info']['dates']['posted']),
            'latitude':             photo['info']['location']['latitude'],
            'longitude':            photo['info']['location']['longitude'],
            'raw':                  json.dumps(photo['info']),

            # Photo fields
            'user':                 user_obj,
            'flickr_id':            photo['info']['id'],
            'description':          photo['info']['description']['_content'],
            'secret':               photo['info']['secret'],
            'orginal_secret':       photo['info']['originalsecret'],
            'server':               photo['info']['server'],
            'farm':                 photo['info']['farm'],
            'license':              photo['info']['license'],
            'rotation':             photo['info']['rotation'],
            'original_format':      photo['info']['originalformat'],
            'safety_level':         photo['info']['safety_level'],
            'has_people':           photo['info']['people']['has_people'],
            'last_update_time':     self._api_unixtime_to_datetime(
                                        photo['info']['dates']['lastupdate']),
            'taken_time':           self._api_datetime_to_datetime(
                                                        photo['dates']['taken'],
                                                        user_obj.timezone_id),
            'taken_granularity':    photo['info']['dates']['takengranularity'],
            'taken_unknown':        photo['info']['dates']['takenunknown'],
            'view_count':           photo['info']['views'],
            'comment_count':        photo['info']['comments']['_content'],
            'media':                photo['info']['media'],

            # Location fields
            'geo_is_private':       (photo['info']['geoperms']['ispublic'] == 0),
            'location_accuracy':    photo['info']['location']['accuracy'],
            'location_context':     photo['info']['location']['context'],
            'location_place_id':    photo['info']['place_id'],
            'location_woe_id':      photo['info']['woeid'],
            'locality_name':        photo['info']['location']['locality']['_content'],
            'locality_place_id':        photo['info']['location']['locality']['place_id'],
            'locality_woe_id':        photo['info']['location']['locality']['woeid'],
            'county_name':        photo['info']['location']['county']['_content'],
            'county_place_id':        photo['info']['location']['county']['place_id'],
            'county_woe_id':        photo['info']['location']['county']['woeid'],
            'region_name':        photo['info']['location']['region']['_content'],
            'region_place_id':        photo['info']['location']['region']['place_id'],
            'region_woe_id':        photo['info']['location']['region']['woeid'],
            'country_name':        photo['info']['location']['country']['_content'],
            'country_place_id':        photo['info']['location']['country']['place_id'],
            'country_woe_id':        photo['info']['location']['country']['woeid'],

            # Sizes fields
            'sizes_raw':            json.dumps(photo['sizes']),

            # EXIF fields
            'exif_raw':             json.dumps(photo['exif']),
            'exif_camera':          photo['exif']['camera'],
        }

        # Go through each of the sizes from the API.
        # If the label (eg, "Small 320") exists, set the size variables
        # (eg, "width_n" and "height_n" with the pixel sizes.
        for size in photo['sizes']['size']:
            variables = photo.get_size_variables(size['label'])
            if len(variables) == 2:
                defaults[variables[0]] = int(size['width'])
                defaults[variables[1]] = int(size['height'])

        try:
            for e in photo['exif']['exif']:
                if e['tag'] == 'LensModel':
                    defaults['exif_lens_model'] == e['raw']['_content']
                elif e['tag'] == 'FNumber':
                    defaults['exif_aperture'] == e['clean']['_content']
                elif e['tag'] == 'ExposureTime':
                    defaults['exif_exposure'] == e['clean']['_content']
                elif e['tag'] == 'Flash':
                    defaults['exif_flash'] == e['raw']['_content']
                elif e['tag'] == 'FocalLength':
                    defaults['exif_focal_length'] == e['clean']['_content']
                elif e['tag'] == 'ISO':
                    defaults['exif_iso'] == e['raw']['_content']
        except KeyError:
            pass

        photo_obj, created = Photo.objects.update_or_create(
                flickr_id=photo['info']['id'],
                defaults=defaults
            )

        # TODO: Add/sync tags.

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
                break
            self.page += 1

        if 'success' in self.return_value and self.return_value['success'] == False:
            # Something went wrong.
            return
        else:
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
    """Parent class for any classes that fetch and then save lists of Photos.
    """

    # Will be the minimum date of upload/fave for Photos that we'll fetch.
    min_date = None

    # Will be 'new' or 'date':
    fetch_type = 'new'

    # 500 is the max the API allows.
    photos_per_page = 5

    # Will match Flickr IDs with their User object.
    # eg '35034346050@N01' => User
    # When we fetch a user's data, because we need it to save a photo/tag,
    # we add their object to this, so we don't fetch again this time.
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

    def _call_api(self):
        """Define in child classes.
        Should call self.api.a_function_name() and set self.results with the
        results.
        """
        raise FetchError("Children of the FetchPhotos class should define their own _call_api() method.")

    def _fetch_extra(self):
        """Before saving we need to go through the big list of photos we've
        fetched, and fetch more detailed info to add to each photo's data.
        """
        extra_results = []

        for i, photo in enumerate(self.results):

            self._fetch_user_if_missing(photo['owner'])

            extra_results.append({
                # Add the data for the photo's owner:
                'user_obj': self.fetched_users[ photo['owner'] ],
                # Get all the info about this photo:
                'info': self._fetch_photo_info(photo['id']),
                'sizes': self._fetch_photo_sizes(photo['id']),
                'exif': self._fetch_photo_exif(photo['id']),
            })

        # Replace self.results with our new array that contains more info.
        self.results = extra_results

    def _fetch_user_if_missing(self, flickr_user_id):
        """
        If we don't have flickr_user_id in self.fetched_users, then fetch, and
        save, that user from the API. Then add their User to self.fetched_users.
        flickr_user_id -- The user's ID on Flickr, eg '35034346050@N01'.
        """
        if self.fetched_users.get(flickr_user_id, None) is None:
            try:
                user_info = self.api.people.getInfo(user_id=flickr_user_id)
            except FlickrError as e:
                raise FetchError("Error when getting info about User with id '%s': %s" % (flickr_user_id, e))

            user_obj = self.save_user(user_info['person'], self.fetch_time)
            self.fetched_users[flickr_user_id] = user_obj

    def _fetch_photo_info(self, photo_id):
        """Calls the photos.getInfo() method of the Flickr API and returns the
        info about the photo.
        https://www.flickr.com/services/api/explore/flickr.photos.getInfo
        photo_id -- The Flickr photo ID.
        """
        try:
            results = self.api.photos.getInfo(photo_id = photo_id)
        except FlickrError as e:
            raise FetchError("Error when fetching photo info (photo %s): %s" % (photo_id, e))

        # Each tag on the photo is added by a specific Flickr user.
        # (Usually, but not always, the photo owner.)
        # Check that we've got info about that user in our DB.
        for tag in results['photo']['tags']['tag']:
            self._fetch_user_if_missing(tag['author'])

        return results['photo']

    def _fetch_photo_sizes(self, photo_id):
        """Calls the photos.getSizes() method of the Flickr API and returns the
        photo's sizes.
        https://www.flickr.com/services/api/explore/flickr.photos.getSizes
        photo_id -- The Flickr photo ID.
        """
        try:
            results = self.api.photos.getSizes(photo_id = photo_id)
        except FlickrError as e:
            raise FetchError("Error when fetching photo sizes (photo %s): %s" % (photo_id, e))

        return results['sizes']

    def _fetch_photo_exif(self, photo_id):
        """Calls the photos.getExif() method of the Flickr API and returns the
        photo's EXIF data.
        https://www.flickr.com/services/api/explore/flickr.photos.getExif
        photo_id -- The Flickr photo ID.
        """
        try:
            results = self.api.photos.getExif(photo_id = photo_id)
        except FlickrError as e:
            raise FetchError("Error when fetching photo EXIF data (photo %s): %s" % (photo_id, e))

        return results['photo']

    def _save_results(self):
        """Save all the data we've fetched about photos to the DB."""
        for photo in self.results:
            p = self.save_photo(photo, self.fetch_time)
            self.objects.append(p)


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

        if self.page == 1 and 'photos' in results and 'pages' in results['photos']:
            # First time, set the total_pages there are to fetch.
            self.total_pages == results['photos']['pages']

        # Add the list of photos' data from this page on to our total list:
        self.results += results['photos']['photo']


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

