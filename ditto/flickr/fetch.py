import calendar
import datetime
import json
import pytz
import time

import flickrapi
from flickrapi.exceptions import FlickrError
from taggit.models import Tag

from .models import Account, Photo, Photoset, User
from ..core.utils import datetime_now

# Classes here:
#
# FetchError
# FlickrUtilsMixin
#
# UserSaver
# PhotoSaver
# PhotosetSaver
#
# Fetcher
#   UserIdFetcher
#   UserFetcher
#   PhotosFetcher
#       RecentPhotosFetcher
#   PhotosetsFetcher
#
# MultiAccountFetcher
#   RecentPhotosMultiAccountFetcher
#   PhotosetsMultiAccountFetcher


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
            'is_pro':       (int(user['ispro']) == 1),
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
            'timezone_id':  user['timezone']['timezone_id'],
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
        Photo object.

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
            'has_people':           (int(photo['info']['people']['haspeople']) == 1),
            'last_update_time':     self._unixtime_to_datetime(
                                        photo['info']['dates']['lastupdate']),
            'taken_time':           self._api_datetime_to_datetime(
                                                photo['info']['dates']['taken'],
                                                photo['user_obj'].timezone_id),
            'taken_granularity':    int(photo['info']['dates']['takengranularity']),
            'taken_unknown':        (int(photo['info']['dates']['takenunknown']) == 1),
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
            defaults['geo_is_private']      = (int(photo['info']['geoperms']['ispublic']) == 0)

        if 'location' in photo['info']:
            loc = photo['info']['location']
            defaults['latitude']            = loc['latitude']
            defaults['longitude']           = loc['longitude']
            defaults['location_accuracy']   = loc['accuracy']
            defaults['location_context']    = loc['context']
            defaults['location_place_id']   = loc['place_id']
            defaults['location_woeid']      = loc['woeid']
            if 'locality' in loc:
                defaults['locality_name']       = loc['locality']['_content']
                defaults['locality_place_id']   = loc['locality']['place_id']
                defaults['locality_woeid']      = loc['locality']['woeid']
            if 'county' in loc:
                defaults['county_name']         = loc['county']['_content']
                defaults['county_place_id']     = loc['county']['place_id']
                defaults['county_woeid']        = loc['county']['woeid']
            if 'region' in loc:
                defaults['region_name']         = loc['region']['_content']
                defaults['region_place_id']     = loc['region']['place_id']
                defaults['region_woeid']        = loc['region']['woeid']
            if 'country' in loc:
                defaults['country_name']        = loc['country']['_content']
                defaults['country_place_id']    = loc['country']['place_id']
                defaults['country_woeid']       = loc['country']['woeid']

        # The size labels for all possible sizes an image might have, that we
        # also have width/height parameters for on Photo:
        sizes = [
            #'Square',
            #'Large square',
            'Thumbnail',
            'Small',
            'Small 320',
            'Medium',
            'Medium 640',
            'Medium 800',
            'Large',
            'Large 1600',
            'Large 2048',
            'Original',
            'Mobile MP4',
            'Site MP4',
            'HD MP4',
            'Video Original',
        ]
        for size in photo['sizes']['size']:
            if size['label'] in sizes:
                # eg, 'Small 320' becomes 'small_320':
                name = size['label'].lower().replace(" ", "_")
                defaults[name+'_width'] = int(size['width'])
                defaults[name+'_height'] = int(size['height'])

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
        tagged_photos = Photo.tags.through.objects.filter(
                                                       content_object=photo_obj)

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


class PhotosetSaver(FlickrUtilsMixin, object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_photoset(self, photoset):
        """Takes a dict of photoset data from the API and creates or updates a
        Photoset object.

        It accepts a list of photo data, but will only add each photo to the
        photoset if we already have that photo's data in the DB.

        Keyword arguments:
        photoset -- Has keys:
                    'fetch_time': A datetime.
                    'photoset': The data about the photoset from the API.
                    'photos': The data about the set's photos from the API.
                    'user_obj': User object for this photoset's owner.

        Returns:
        The Photoset object that was created or updated.
        """

        ps = photoset['photoset']

        defaults = {
            'fetch_time':           photoset['fetch_time'],
            'user':                 photoset['user_obj'],
            'flickr_id':            ps['id'],
            'title':                ps['title']['_content'],
            'description':          ps['description']['_content'],
            'photo_count':          ps['photos'],
            'video_count':          ps['videos'],
            'view_count':           ps['count_views'],
            'comment_count':        ps['count_comments'],
            'last_update_time':     self._unixtime_to_datetime(
                                                            ps['date_update']),
            'flickr_created_time':  self._unixtime_to_datetime(
                                                            ps['date_create']),
            'raw':                  json.dumps(ps),
            'photos_raw':          json.dumps(photoset['photos']),
        }

        try:
            defaults['primary_photo'] = \
                                    Photo.objects.get(flickr_id=ps['primary'])
        except Photo.DoesNotExist:
            pass

        photoset_obj, created = Photoset.objects.update_or_create(
                flickr_id=ps['id'],
                defaults=defaults
            )

        if photoset_obj:
            # Add all the photoset's photos that we have in the DB to the
            # photoset object.
            photos = []
            for photo in photoset['photos']:
                try:
                    photos.append( Photo.objects.get(flickr_id=photo['id']) )
                except Photo.DoesNotExist:
                    pass

            # Sets/updates the SortedManyToMany field of the photoset's photos:
            photoset_obj.photos = photos

        return photoset_obj



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


class UserIdFetcher(Fetcher):
    """Returns the Flickr ID for an Account's user.
    Doesn't save anything.

    Use like:
        results = UserIdFetcher(account=account_obj).fetch()

    Results will look something like:
        {'id': '35034346050@N01', 'fetched': 1, 'account': 'Phil Gyford', 'success': True}
    """

    def _call_api(self):
        """Calls test.login() to get the very basic user info for the
        authenticating user.
        Docs: https://www.flickr.com/services/api/flickr.test.login.htm
        """
        try:
            info = self.api.test.login()
        except FlickrError as e:
            raise FetchError("Error when calling test.login(): %s'" % e)

        self.results = [ {'id': info['user']['id']} ]

    def _save_results(self):
        "Doesn't save any results, just prepares to return the Flickr ID."
        self.return_value['id'] = self.results[0]['id']
        self.results_count = 1


class UserFetcher(Fetcher):
    """Fetches and saves data about a single User by Flickr ID."""

    def fetch(self, nsid=None):
        """Fetches and saves data about a single User by Flickr ID.
        nsid -- A Flickr ID for a user.
        """
        if nsid is None:
            raise FetchError(
                        "UserFetcher().fetch() requires a Flickr id (NSID)")

        return super().fetch(nsid=nsid)

    def _call_api(self, nsid):
        "nsid -- A Flickr ID for a user."
        try:
            info = self.api.people.getInfo(user_id=nsid)
        except FlickrError as e:
            raise FetchError(
                "Error when getting info about User with Flickr ID '%s': %s" %\
                                                                    (nsid, e))

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
        days -- Required. The number of days back to look, by upload date, or
                'all' to fetch all photos.
        """
        try:
            self.min_date = datetime_now() - datetime.timedelta(days=days)
        except TypeError:
            if days != 'all':
                raise FetchError("days should be a number or 'all'.")

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


#class FavoritePhotosFetcher(PhotosFetcher):
    #"""Fetches and saves data about an Account's favorite Photos.

    #By default ALL favorite photos will be fetched.

    #Supply a number of days to fetch() to restrict to the photos favorited in
    #the most recent days.
    #"""

    #def fetch(self, days=None):
        #"""Fetch all of the Account's user's photos, by default.
        #days -- The number of days back to look, by upload date.
        #"""
        #if days is not None:
            #self.min_date = datetime_now() - datetime.timedelta(days=days)

        #return super().fetch()

    #def _call_api(self):
        #"""Fetch one page of results, containing very basic info about the
        #Photos."""

        ## Turn our datetime object into a unix timestamp:
        #min_unixtime = calendar.timegm(self.min_date.timetuple())

        #try:
            #results = self.api.people.getPhotos(
                                            #user_id=self.account.user.nsid,
                                            #min_upload_date=min_unixtime,
                                            #per_page=self.items_per_page,
                                            #page=self.page_number
                                        #)
        #except FlickrError as e:
            #raise FetchError(
                #"Error when fetching recent photos (page %s): %s" % \
                                                        #(self.page_number, e))

        #if self.page_number == 1 and 'photos' in results and 'pages' in results['photos']:
            ## First time, set the total_pages there are to fetch.
            #self.total_pages = int(results['photos']['pages'])


        ## Add the list of photos' data from this page on to our total list:
        #self.results += results['photos']['photo']


class PhotosetsFetcher(Fetcher):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Photosets come in pages.
        self.is_paged = True

    def _call_api(self):
        """Fetch one page of results.

        https://www.flickr.com/services/api/flickr.photosets.getList.htm
        """

        try:
            results = self.api.photosets.getList(
                                            user_id=self.account.user.nsid,
                                            per_page=self.items_per_page,
                                            page=self.page_number
                                        )
        except FlickrError as e:
            raise FetchError(
                "Error when fetching photosets (page %s): %s" % \
                                                        (self.page_number, e))

        if self.page_number == 1 and 'photosets' in results and 'pages' in results['photosets']:
            # First time, set the total_pages there are to fetch.
            self.total_pages = int(results['photosets']['pages'])


        # Add the list of photosets' data from this page on to our total list:
        self.results += results['photosets']['photoset']

    def _fetch_extra(self):
        """Before saving we need to get the list of photos in each photoset."""

        extra_results = []

        for i, photoset in enumerate(self.results):

            photos = self._fetch_photos_in_photoset(photoset['id'])

            extra_results.append({
                'fetch_time': datetime_now(),
                'photoset': photoset,
                'photos': photos,
                'user_obj': self.account.user,
            })

        # Replace self.results with our new array that contains more info.
        self.results = extra_results

    def _fetch_photos_in_photoset(self, photoset_id):
        """Gets the info about all the photos in the photoset.
        Might be in multiple pages.
        The data is quite minimal, but that's all we need.

        https://www.flickr.com/services/api/flickr.photosets.getPhotos.htm

        Expects:
            photoset_id -- eg 72157665648859705
        Returns:
            list of dicts, each dict containing photo data
        """

        photos = []
        page_number = 1
        total_pages = 1 # Will get set to its proper value below.

        while page_number <= total_pages:
            try:
                results = self.api.photosets.getPhotos(
                                                photoset_id=photoset_id,
                                                user_id=self.account.user.nsid,
                                                per_page=self.items_per_page,
                                                page=page_number
                                            )
            except FlickrError as e:
                raise FetchError(
                    "Error when fetching photos in photoset %s (page %s): %s"%\
                                                (photoset_id, page_number, e))

            if 'photoset' in results and 'photo' in results['photoset']:
                total_pages = results['photoset']['pages']
                photos += results['photoset']['photo']

            page_number += 1
            time.sleep(1) # Being nice.

        return photos

    def _save_results(self):
        """Save all the data we've fetched about photosets to the DB."""
        saver = PhotosetSaver()
        for photoset in self.results:
            p = saver.save_photoset(photoset)
        self.results_count = len(self.results)

###########################################################################


class MultiAccountFetcher(object):
    """Parent class for fetching things from Flickr for ALL or ONE Account(s).

    Its child classes are useful for:
        * Fetching from all accounts.
        * Fetching from a single account with identical interface and response
          as when fetching from all accounts (otherwise you could use the
          single account fetcher, like RecentPhotosFetcher()).
        * Fetching from a single account when you only have the user's NSID.

    Use something like:

        results = ChildMultiAccountFetcher().fetch(foo=3)

    or:

        results = ChildMultiAccountFetcher(nsid='35034346050@N01').fetch(foo=3)
    """

    # Will be a list of Account objects.
    accounts = []

    def __init__(self, nsid=None):
        """Gets all of the Accounts that child classes will loop through.

        nsid -- If nsid is set, we use only the Account associated with the
                User with that nsid (if it's active). Otherwise, we use all
                active Accounts.
        """
        self.return_value = []

        if nsid is None:
            # Get all active Accounts.
            self.accounts = list(Account.objects.filter(is_active=True))
            if len(self.accounts) == 0:
                raise FetchError("No active Accounts were found to fetch.")
        else:
            # Find the Account associated with nsid.
            try:
                user = User.objects.get(nsid=nsid)
            except User.DoesNotExist:
                raise FetchError("There is no User with the NSID '%s'" % nsid)
            try:
                account = Account.objects.get(user=user)
            except Account.DoesNotExist:
                raise FetchError("There is no Account associated with the User with NSID '%s'" % nsid)
            if account.is_active == False:
                raise FetchError("The Account associated with the User with NSID '%s' is marked as inactive.")

            self.accounts = [account]
        return super().__init__()

    def fetch(self, **kwargs):
        raise FetchError(
            "Subclasess of MultiAccountFetcher should define their own fetch().")


class RecentPhotosMultiAccountFetcher(MultiAccountFetcher):
    """For fetching recent photos for ALL or ONE account(s).

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


class PhotosetsMultiAccountFetcher(MultiAccountFetcher):
    """For fetching ALL photosets for ALL or ONE account(s).

    Usage:

        results = PhotosetsMultiAccountFetcher().fetch()

    results will be a list of dicts containing info about what was fetched (or
    went wrong) for each account.
    """

    def fetch(self):
        for account in self.accounts:
            self.return_value.append(
                PhotosetsFetcher(account).fetch()
            )

        return self.return_value

