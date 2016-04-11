import calendar
import datetime
import json
import pytz
import time

import flickrapi
from flickrapi.exceptions import FlickrError
from taggit.models import Tag

from .models import Account, Photo, User
from ..ditto.utils import datetime_now

# Classes here:
#
# FetchError
# FlickrUtilsMixin
#
# UserSaver
# PhotoSaver
#
# Fetcher
#   UserFetcher
#   PhotosFetcher
#       RecentPhotosFetcher


class FetchError(Exception):
    pass


class FlickrUtilsMixin(object):
    """Handy utility methods."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _api_datetime_to_datetime(self, api_time, timezone_id=None):
        """Change a text datetime from the API to a datetime with timezone.
        api_time is a string like "1956-01-01 00:00:00".
        timezone_id is a TZ timezone name like 'Africa/Accra'
        """
        if timezone_id is None or timezone_id == '':
            timezone_id = 'Etc/UTC'
        tz = pytz.timezone(timezone_id)
        return datetime.datetime.strptime(
                            api_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz)

    def _unixtime_to_datetime(self, api_time):
        """Change a text unixtime from the API to a datetime with timezone.
        api_time is a string or int like "1093459273".
        """
        return datetime.datetime.utcfromtimestamp(
                                        int(api_time)).replace(tzinfo=pytz.utc)


###########################################################################


class UserSaver(FlickrUtilsMixin, object):
    """For creating/updating an individual User based on data from the API.

    Use like:

        UserSaver().save_user(data, fetch_time)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_user(self, user, fetch_time):
        """
        Keyword arguments:
        user -- A dict of the data about a user from the API's JSON.
        fetch_time -- A datetime.

        Returns the User object that was created or updated.
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
            'photos_first_date': self._unixtime_to_datetime(
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


class PhotoSaver(FlickrUtilsMixin, object):
    """For creating/updating an individual Photo based on data from the API.

    Use like:

        PhotoSaver().save_photo(data, fetch_time)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_photo(self, photo):
        """Takes a dict of photo data from the API and creates or updates a
        Photo object and its associated User object.

        Keyword arguments:
        photo -- The photo data, from several Flickr API calls.
                 Has keys:
                     'fetch_time': A datetime.
                     'user_obj': User object for this photo's owner.
                     'info': Results of a photos.getInfo call.
                     'exif': Results of a photos.getExif call.
                     'sizes': Results of a photos.getSizes call.

        Returns:
        The Photo object that was created or updated.
        """

        # photo['info']['urls'] = {
        #     'url': [ {'type':'photopage', '_content':'http...'} ]
        # }
        permalink = next(url for url in photo['info']['urls']['url'] if url['type'] == 'photopage')['_content']

        defaults = {
            # DittoItemModel fields
            'title':                photo['info']['title']['_content'],
            'permalink':            permalink,
            'is_private':           (photo['info']['visibility']['ispublic'] == 0),
            'fetch_time':           photo['fetch_time'],
            'post_time':            self._unixtime_to_datetime(
                                            photo['info']['dates']['posted']),
            'raw':                  json.dumps(photo['info']),

            # Photo fields
            'user':                 photo['user_obj'],
            'flickr_id':            photo['info']['id'],
            'description':          photo['info']['description']['_content'],
            'secret':               photo['info']['secret'],
            'original_secret':      photo['info']['originalsecret'],
            'server':               photo['info']['server'],
            'farm':                 photo['info']['farm'],
            'license':              photo['info']['license'],
            'rotation':             photo['info']['rotation'],
            'original_format':      photo['info']['originalformat'],
            'safety_level':         photo['info']['safety_level'],
            'has_people':           photo['info']['people']['haspeople'],
            'last_update_time':     self._unixtime_to_datetime(
                                        photo['info']['dates']['lastupdate']),
            'taken_time':           self._api_datetime_to_datetime(
                                                photo['info']['dates']['taken'],
                                                photo['user_obj'].timezone_id),
            'taken_granularity':    photo['info']['dates']['takengranularity'],
            'taken_unknown':        photo['info']['dates']['takenunknown'],
            'view_count':           photo['info']['views'],
            'comment_count':        photo['info']['comments']['_content'],
            'media':                photo['info']['media'],

            # Location fields

            # Sizes fields
            'sizes_raw':            json.dumps(photo['sizes']),

            # EXIF fields
            'exif_raw':             json.dumps(photo['exif']),
            'exif_camera':          photo['exif']['camera'],
        }

        # Photos with no location have these fields missing entirely:
        if 'geoperms' in photo['info']:
            defaults['geo_is_private']      = (photo['info']['geoperms']['ispublic'] == 0)

        if 'location' in photo['info']:
            defaults['latitude']            = photo['info']['location']['latitude']
            defaults['longitude']           = photo['info']['location']['longitude']
            defaults['location_accuracy']   = photo['info']['location']['accuracy']
            defaults['location_context']    = photo['info']['location']['context']
            defaults['location_place_id']   = photo['info']['location']['place_id']
            defaults['location_woeid']      = photo['info']['location']['woeid']
            defaults['locality_name']       = photo['info']['location']['locality']['_content']
            defaults['locality_place_id']   = photo['info']['location']['locality']['place_id']
            defaults['locality_woeid']      = photo['info']['location']['locality']['woeid']
            defaults['county_name']         = photo['info']['location']['county']['_content']
            defaults['county_place_id']     = photo['info']['location']['county']['place_id']
            defaults['county_woeid']        = photo['info']['location']['county']['woeid']
            defaults['region_name']         = photo['info']['location']['region']['_content']
            defaults['region_place_id']     = photo['info']['location']['region']['place_id']
            defaults['region_woeid']        = photo['info']['location']['region']['woeid']
            defaults['country_name']        = photo['info']['location']['country']['_content']
            defaults['country_place_id']    = photo['info']['location']['country']['place_id']
            defaults['country_woeid']       = photo['info']['location']['country']['woeid']

        # Go through each of the sizes from the API.
        # If the label (eg, "Small 320") exists, set the size variables
        # (eg, "width_n" and "height_n" with the pixel sizes.
        for size in photo['sizes']['size']:
            variables = Photo().get_size_variables(size['label'])
            if len(variables) == 2:
                defaults[variables[0]] = int(size['width'])
                defaults[variables[1]] = int(size['height'])

        try:
            import logging
            for e in photo['exif']['exif']:
                if e['tag'] == 'LensModel':
                    defaults['exif_lens_model'] = e['raw']['_content']
                elif e['tag'] == 'FNumber':
                    defaults['exif_aperture'] = e['clean']['_content']
                elif e['tag'] == 'ExposureTime':
                    defaults['exif_exposure'] = e['clean']['_content']
                elif e['tag'] == 'Flash':
                    defaults['exif_flash'] = e['raw']['_content']
                elif e['tag'] == 'FocalLength':
                    defaults['exif_focal_length'] = e['clean']['_content']
                elif e['tag'] == 'ISO':
                    defaults['exif_iso'] = e['raw']['_content']
        except KeyError:
            pass

        photo_obj, created = Photo.objects.update_or_create(
                flickr_id=photo['info']['id'],
                defaults=defaults
            )

        self._save_tags(photo_obj, photo['info']['tags']['tag'])

        return photo_obj

    def _save_tags(self, photo_obj, tags_data):
        """
        Adds/deletes tags for a photo.

        Required Arguments
          photo_obj: The Photo object we're altering tags for.
          photo_user_obj: The User whose photo this is (because they're most
                            likely to have created the tags.)
          tags_data: A list of dicts about the tags, straight from the API.
        """

        # The existing tag-photo relationships.
        tagged_photos = Photo.tags.through.objects.filter(content_object=photo_obj)

        local_flickr_ids = set([])
        remote_flickr_ids = set([])

        # Get the Flickr IDs of all the current tag-photo relationships.
        for tagged_photo in tagged_photos:
            local_flickr_ids.add(tagged_photo.flickr_id)

        for tag in tags_data:
            remote_flickr_ids.add(tag['id'])

            if tag['id'] not in local_flickr_ids:

                # This tag isn't currently on the photo, so add it.
                tag_obj, tag_created = Tag.objects.get_or_create(
                    slug=tag['_content'], defaults={ 'name':tag['raw'] }
                )

                # Who created this tag?
                if tag['author'] == photo_obj.user.nsid:
                    # The same person whose photo these tags are on.
                    user = photo_obj.user
                else:
                    # In theory we'll already have fetched and saved data for
                    # all authors of these tags when fetching this photo's
                    # data.
                    try:
                        user = User.objects.get(nsid=tag['author'])
                    except User.DoesNotExist:
                        raise FetchError("Tried to add a Tag authored by a Flickr user with NSID %s who doesn't exist in the DB." % tag['author'])

                pt_obj = Photo.tags.through(
                            flickr_id = tag['id'],
                            author = user,
                            machine_tag = (tag['machine_tag'] == "1"),
                            content_object = photo_obj,
                            tag = tag_obj
                        )
                pt_obj.save()

        flickr_ids_to_delete = local_flickr_ids.difference(remote_flickr_ids)

        # Finally, delete any tag-photo relationships which were identified
        # above as no longer on the photo on Flickr.
        for tagged_photo in tagged_photos:
            if tagged_photo.flickr_id in flickr_ids_to_delete:
                tagged_photo.delete()

###########################################################################


class Fetcher(object):
    """Parent class for children that will call the Flickr API to fetch data.

    Depending on the child classes, it would be used something like:

        results = Fetcher(account=account_object).fetch()

    results is a dict that will have:
        'success': Boolean.
        'account': String. Indicating the Account (eg, its User's username).
        'fetched': Integer. If success, the number of things fetched, if any.
        'message': String. If no success, the failure message.
    """

    # How many photos (or whatever) do we fetch per page of retults?
    items_per_page = 500

    def __init__(self, account):
        # Will be an Account object, passed into init()
        self.account = None

        # Will be the FlickrAPI object for calling the Flickr API.
        self.api = None

        # Are the things we're fetching in (possibly) multiple pages?
        self.is_paged = False

        # Will be incremented if we're fetching multiple pages.
        self.page_number = 1

        # If there are multiple pages to fetch, this should be set when we get
        # the first page.
        self.total_pages = 1

        # Will be the minimum date of upload/fave for Photos that we'll fetch.
        # By default, set it before Flickr so we get everything.
        self.min_date = datetime.datetime.strptime('2000-01-01', '%Y-%m-%d')

        # Will be the results fetched from the API via FlickrAPI.
        self.results = []

        # When fetching Photos or Users this will be the total number fetched.
        self.results_count = 0

        # What we'll return:
        self.return_value = {'fetched': 0}

        if account.user:
            self.return_value['account'] = account.user.username
        elif account.pk:
            self.return_value['account'] = 'Account: %s' % str(account)
        else:
            self.return_value['account'] = 'Unsaved Account'

        if account.has_credentials():
            self.account = account
            self.api = flickrapi.FlickrAPI(self.account.api_key,
                                self.account.api_secret, format='parsed-json')
        else:
            self.return_value['success'] = False
            self.return_value['message'] = 'Account has no API credentials'

    def fetch(self, **kwargs):
        if self.account is None:
            if 'success' not in self.return_value:
                self.return_value['success'] = False
                self.return_value['message'] = 'No Account has been set'
        else:
            if self.is_paged:
                self._fetch_pages(**kwargs)
            else:
                self._fetch_page(**kwargs)

            if self._not_failed():
                # OK so far; get extra data, if any, before saving.
                try:
                    self._fetch_extra()
                except FetchError as e:
                    self.return_value['success'] = False
                    self.return_value['message'] = 'Error when fetching extra data: %s' % e

            if self._not_failed():
                # Still OK; save the data we've got.
                try:
                    self._save_results()
                    self.return_value['success'] = True
                    self.return_value['fetched'] += self.results_count
                except FetchError as e:
                    self.return_value['success'] = False
                    self.return_value['message'] = 'Error when saving data: %s' % e

        return self.return_value

    def _fetch_pages(self, **kwargs):
        """Fetch all of the pages.
        This relies on something else setting self.total_pages to the correct
        value. Probably in _call_api(), set it when fetching the first page,
        as the results will contain the total number of pages available.
        """
        while self.page_number <= self.total_pages and self._not_failed():
            self._fetch_page(**kwargs)
            self.page_number += 1
            time.sleep(1) # Being nice.

    def _fetch_page(self, **kwargs):
        try:
            self._call_api(**kwargs)
        except FetchError as e:
            self.return_value['success'] = False
            self.return_value['message'] = 'Error when calling Flickr API: %s' % e

    def _not_failed(self):
        """Has everything gone smoothly so far? ie, no failure registered?"""
        if 'success' not in self.return_value or self.return_value['success'] == True:
            return True
        else:
            return False

    def _call_api(self, **kwargs):
        """
        Should call self.api.a_function() and set self.results with the results.
        """
        raise FetchError(
            "Subclasess of Fetcher should define their own _call_api().")

    def _fetch_extra(self):
        """Can be defined in subclasses to fetch extra data to add to
        self.results before we save the data in the DB."""
        pass

    def _save_results(self, **kwargs):
        """
        Should go through self.results and create/update things in the DB based
        on its contents.
        """
        raise FetchError(
            "Subclasses of Fetcher should define their own _save_results().")


class UserFetcher(Fetcher):
    """Fetches and saves data about a single User."""

    def fetch(self, url=None):
        """
        url -- A Flickr URL owned by a user,
                eg 'https://www.flickr.com/photos/philgyford/8102921/'
        """
        return super().fetch(url=url)

    def _call_api(self, **kwargs):
        url = kwargs.get('url', None)

        if url is None:
            raise FetchError("UserFetcher._call_api() requires a url.")

        try:
            # First, get the user's NSID using the URL:
            user = self.api.urls.lookupUser(url=url)
        except FlickrError as e:
            raise FetchError("Error when looking up user with URL '%s': %s" % \
                                                                    (url, e))
        try:
            # Now we can get the user's info:
            info = self.api.people.getInfo(user_id=user['user']['id'])
        except FlickrError as e:
            raise FetchError(
                "Error when getting info about User with id '%s': %s" % \
                                                    (user['user']['id'], e))

        # info has 'person' and 'stat' elements.
        self.results = [ info['person'] ]

    def _save_results(self):
        user_obj = UserSaver().save_user(self.results[0], datetime_now())
        self.return_value['user'] = {'name': user_obj.name}
        self.results_count = 1


class PhotosFetcher(Fetcher):
    """Parent class for fetching and saving data about Photos for an Account.
    """

    def __init__(self, *args, **kwargs):
        # Will match Flickr IDs with their User object.
        # eg '35034346050@N01' => User
        # When we fetch a user's data, because we need it to save a photo/tag,
        # we add their object to this, so we don't fetch again this time.
        self.fetched_users = {}

        super().__init__(*args, **kwargs)

        # Photos come in pages.
        self.is_paged = True

    def _call_api(self):
        """
        Should call self.api.a_function() and set self.results with the results.
        """
        raise FetchError(
            "Subclasess of PhotosFetcher should define their own _call_api().")

    def _fetch_extra(self):
        """Before saving we need to go through the big list of photos we've
        fetched, and fetch more detailed info to add to each photo's data.
        """
        extra_results = []

        for i, photo in enumerate(self.results):

            self._fetch_user_if_missing(photo['owner'])

            extra_results.append({
                'fetch_time': datetime_now(),
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
                raise FetchError(
                    "Error when getting info about User with id '%s': %s" % \
                                                        (flickr_user_id, e))

            user_obj = UserSaver().save_user(user_info['person'], datetime_now())
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
            raise FetchError("Error when fetching photo info (photo %s): %s" % \
                                                                (photo_id, e))

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
            raise FetchError(
                "Error when fetching photo sizes (photo %s): %s" % \
                                                                (photo_id, e))
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
            raise FetchError(
                "Error when fetching photo EXIF data (photo %s): %s" % \
                                                                (photo_id, e))
        return results['photo']

    def _save_results(self):
        """Save all the data we've fetched about photos to the DB."""
        saver = PhotoSaver()
        for photo in self.results:
            p = saver.save_photo(photo)
        self.results_count = len(self.results)


class RecentPhotosFetcher(PhotosFetcher):
    """Fetches and saves data about an Account's recent Photos.

    By default ALL photos will be fetched.

    Supply a number of days to fetch() to restrict to the most recent days.
    """

    def fetch(self, days=None):
        """Fetch all of the Account's user's photos, by default.
        days -- The number of days back to look, by upload date.
        """
        if days is not None:
            self.min_date = datetime_now() - datetime.timedelta(days=days)

        return super().fetch()

    def _call_api(self):
        """Fetch one page of results, containing very basic info about the
        Photos."""

        # Turn our datetime object into a unix timestamp:
        min_unixtime = calendar.timegm(self.min_date.timetuple())

        try:
            results = self.api.people.getPhotos(
                                            user_id=self.account.user.nsid,
                                            min_upload_date=min_unixtime,
                                            per_page=self.items_per_page,
                                            page=self.page_number
                                        )
        except FlickrError as e:
            raise FetchError(
                "Error when fetching recent photos (page %s): %s" % \
                                                        (self.page_number, e))

        if self.page_number == 1 and 'photos' in results and 'pages' in results['photos']:
            # First time, set the total_pages there are to fetch.
            self.total_pages = int(results['photos']['pages'])


        # Add the list of photos' data from this page on to our total list:
        self.results += results['photos']['photo']


class FavoritePhotosFetcher(PhotosFetcher):
    """Fetches and saves data about an Account's favorite Photos.

    By default ALL favorite photos will be fetched.

    Supply a number of days to fetch() to restrict to the photos favorited in
    the most recent days.
    """

    def fetch(self, days=None):
        """Fetch all of the Account's user's photos, by default.
        days -- The number of days back to look, by upload date.
        """
        if days is not None:
            self.min_date = datetime_now() - datetime.timedelta(days=days)

        return super().fetch()

    def _call_api(self):
        """Fetch one page of results, containing very basic info about the
        Photos."""

        # Turn our datetime object into a unix timestamp:
        min_unixtime = calendar.timegm(self.min_date.timetuple())

        try:
            results = self.api.people.getPhotos(
                                            user_id=self.account.user.nsid,
                                            min_upload_date=min_unixtime,
                                            per_page=self.items_per_page,
                                            page=self.page_number
                                        )
        except FlickrError as e:
            raise FetchError(
                "Error when fetching recent photos (page %s): %s" % \
                                                        (self.page_number, e))

        if self.page_number == 1 and 'photos' in results and 'pages' in results['photos']:
            # First time, set the total_pages there are to fetch.
            self.total_pages = int(results['photos']['pages'])


        # Add the list of photos' data from this page on to our total list:
        self.results += results['photos']['photo']


###########################################################################


class MultiAccountFetcher(object):
    """Parent class for fetching things from Flickr for multiple Accounts.
    
    Use something like:
        
        results = ChildMultiAccountFetcher().fetch(foo=bar)
    """

    def __init__(self):
        """Gets all of the active accounts that child classes will loop through.
        """
        self.return_value = []

        self.accounts = Account.objects.filter(is_active=True)
        if len(self.accounts) == 0:
            raise FetchError("No active Accounts were found to fetch.")
        return super().__init__()

    def fetch(self, **kwargs):
        raise FetchError(
            "Subclasess of MultiAccountFetcher should define their own fetch().")


class RecentPhotosMultiAccountFetcher(MultiAccountFetcher):
    """For fetching recent photos for ALL accounts.

    Usage:

        results = RecentPhotosMultiAccountFetcher().fetch(days=7)

    Or omit the `days` to fetch ALL photos for ALL accounts.

    results will be a list of dicts containing info about what was fetched (or
    went wrong) for each account.
    """

    def fetch(self, days=None):
        for account in self.accounts:
            self.return_value.append(
                RecentPhotosFetcher(account).fetch(days=days)
            )

        return self.return_value


