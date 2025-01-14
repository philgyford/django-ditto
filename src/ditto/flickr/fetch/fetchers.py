import calendar
import datetime
import os
import time

import flickrapi
from django.core.files import File
from flickrapi.exceptions import FlickrError

from ditto.core.utils import datetime_now
from ditto.core.utils.downloader import DownloadException, filedownloader
from ditto.flickr.models import Account, User

from . import FetchError
from .savers import PhotoSaver, PhotosetSaver, UserSaver

# These classes call the Flickr API to fetch data about particular things,
# from the point of view of a single Account. eg, Photos, Users, Photosets.
#
# This data is then passed on to *Saver classes for creation/updating of
# objects.

# CLASSES HERE:
#
# Fetcher
#   UserIdFetcher
#   UserFetcher
#   PhotosFetcher
#       RecentPhotosFetcher
#   PhotosetsFetcher


class Fetcher:
    """Parent class for children that will call the Flickr API to fetch data.

    Depending on the child classes, it would be used something like:

        results = Fetcher(account=account_object).fetch()

    results is a dict that will have:
        'success': Boolean.
        'account': String. Indicating the Account (eg, its User's username).
        'fetched': Integer. If success, the number of things fetched, if any.
        'messages': List. If no success, the failure message(s).
    """

    # How many photos (or whatever) do we fetch per page of retults?
    items_per_page = 500

    def __init__(self, account):
        # Will be an Account object, passed into init()
        self.account = None

        # Will be the FlickrAPI object for calling the Flickr API.
        self.api = None

        # Will be incremented if we're fetching multiple pages.
        self.page_number = 1

        # If there are multiple pages to fetch, this should be set when we get
        # the first page.
        self.total_pages = 1

        # Will be the results fetched from the API via FlickrAPI.
        self.results = []

        # When fetching Photos or Users this will be the total number fetched.
        self.results_count = 0

        # What we'll return:
        self.return_value = {"fetched": 0}

        if isinstance(account, Account):
            if account.user:
                self.return_value["account"] = account.user.username
            elif account.pk:
                self.return_value["account"] = f"Account: {account}"
            else:
                self.return_value["account"] = "Unsaved Account"
        else:
            msg = "An Account object is required"
            raise ValueError(msg)

        if account.has_credentials():
            self.account = account
            self.api = flickrapi.FlickrAPI(
                self.account.api_key, self.account.api_secret, format="parsed-json"
            )
        else:
            self.return_value["success"] = False
            self.return_value["messages"] = ["Account has no API credentials"]

    def fetch(self, **kwargs):
        self._fetch_pages(**kwargs)

        if self._not_failed():
            self.return_value["success"] = True
            self.return_value["fetched"] = self.results_count

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
            time.sleep(0.5)  # Being nice.

    def _fetch_page(self, **kwargs):
        try:
            self._call_api(**kwargs)
        except FetchError as e:
            self.return_value["success"] = False
            self.return_value["messages"] = [f"Error when calling Flickr API: {e}"]
            return

        try:
            self._fetch_extra()
        except FetchError as e:
            self.return_value["success"] = False
            self.return_value["messages"] = [f"Error when fetching extra data: {e}"]
            return

        try:
            self._save_results()
            # Clear for the next page:
            self.results = []
        except FetchError as e:
            self.return_value["success"] = False
            self.return_value["messages"] = [f"Error when saving data: {e}"]
            return

        return

    def _not_failed(self):
        """Has everything gone smoothly so far? ie, no failure registered?"""
        return (
            "success" not in self.return_value or self.return_value["success"] is True
        )

    def _call_api(self, **kwargs):
        """
        Should call self.api.a_function() and set self.results with the results.
        """
        msg = "Subclasess of Fetcher should define their own _call_api()."
        raise FetchError(msg)

    def _fetch_extra(self):
        """Can be defined in subclasses to fetch extra data to add to
        self.results before we save the data in the DB."""

    def _save_results(self, **kwargs):
        """
        Should go through self.results and create/update things in the DB based
        on its contents.
        """
        msg = "Subclasses of Fetcher should define their own _save_results()."
        raise FetchError(msg)


class UserIdFetcher(Fetcher):
    """Returns the Flickr ID for an Account's user.
    Doesn't save anything.

    Use like:
        results = UserIdFetcher(account=account_obj).fetch()

    Results will look something like:
        {
            'id': '35034346050@N01',
            'fetched': 1,
            'account': 'Phil Gyford',
            'success': True,
        }
    """

    def _call_api(self):
        """Calls test.login() to get the very basic user info for the
        authenticating user.
        Docs: https://www.flickr.com/services/api/flickr.test.login.htm
        """
        try:
            info = self.api.test.login()
        except FlickrError as err:
            msg = f"Error when calling test.login(): {err}'"
            raise FetchError(msg) from err

        self.results = [{"id": info["user"]["id"]}]

    def _save_results(self):
        "Doesn't save any results, just prepares to return the Flickr ID."
        self.return_value["id"] = self.results[0]["id"]
        self.results_count = 1


class UserFetcher(Fetcher):
    """Fetches and saves data about a single User by Flickr ID."""

    def fetch(self, nsid=None):
        """Fetches and saves data about a single User by Flickr ID.
        nsid -- A Flickr ID for a user.
        """
        if nsid is None:
            msg = "UserFetcher().fetch() requires a Flickr id (NSID)"
            raise FetchError(msg)

        return super().fetch(nsid=nsid)

    def _call_api(self, nsid):
        "nsid -- A Flickr ID for a user."
        try:
            info = self.api.people.getInfo(user_id=nsid)
        except FlickrError as err:
            # User has deleted their account, so create a dummy result
            if err.code == 5:
                self.results = [
                    {
                        "raw": "{}",
                        "nsid": nsid,
                        "username": {"_content": "deleted_user_" + nsid},
                        "photos": {
                            "count": {"_content": "0"},
                            "firstdate": {"_content": "0"},
                            "firstdatetaken": {"_content": "1970-01-01 00:00:00"},
                        },
                    }
                ]
                return

            msg = f"Error when getting info about User with Flickr ID '{nsid}': {err}"
            raise FetchError(msg) from err

        # info has 'person' and 'stat' elements.
        self.results = [info["person"]]

    def _save_results(self):
        user_obj = UserSaver().save_user(self.results[0], datetime_now())
        self._fetch_and_save_avatar(user_obj)
        self.return_value["user"] = {"name": user_obj.name}
        self.results_count = 1

    def _fetch_and_save_avatar(self, user):
        """
        Download and save the Avatar/profile pic for this user.
        user -- User object.
        """
        try:
            avatar_filepath = filedownloader.download(
                user.original_icon_url,
                ["image/jpeg", "image/jpg", "image/png", "image/gif"],
            )

            with open(avatar_filepath, "rb") as f:
                user.avatar.save(os.path.basename(avatar_filepath), File(f))
        except DownloadException:
            pass


class PhotosFetcher(Fetcher):
    """Parent class for fetching and saving data about Photos for an Account."""

    def __init__(self, *args, **kwargs):
        # Will match Flickr IDs with their User object.
        # eg '35034346050@N01' => User
        # When we fetch a user's data, because we need it to save a photo/tag,
        # we add their object to this, so we don't fetch again this time.
        self.fetched_users = {}

        super().__init__(*args, **kwargs)

    def _call_api(self):
        """
        Should call self.api.a_function() and set self.results with the results.
        """
        msg = "Subclasess of PhotosFetcher should define their own _call_api()."
        raise FetchError(msg)

    def _fetch_extra(self):
        """Before saving we need to go through the big list of photos we've
        fetched, and fetch more detailed info to add to each photo's data.
        """
        extra_results = []

        for _i, photo in enumerate(self.results):
            self._fetch_user_if_missing(photo["owner"])

            extra_results.append(
                {
                    "fetch_time": datetime_now(),
                    # Add the data for the photo's owner:
                    "user_obj": self.fetched_users[photo["owner"]],
                    # Get all the info about this photo:
                    "info": self._fetch_photo_info(photo["id"]),
                    "sizes": self._fetch_photo_sizes(photo["id"]),
                    "exif": self._fetch_photo_exif(photo["id"]),
                }
            )

        # Replace self.results with our new array that contains more info.
        self.results = extra_results

    def _fetch_user_if_missing(self, flickr_user_id):
        """
        If we don't have flickr_user_id in self.fetched_users, then fetch, and
        save, that user from the API. Then add their User to self.fetched_users.
        flickr_user_id -- The user's ID on Flickr, eg '35034346050@N01'.
        """
        if self.fetched_users.get(flickr_user_id, None) is None:
            results = UserFetcher(account=self.account).fetch(nsid=flickr_user_id)
            if results["success"] is False:
                raise FetchError(results["messages"][0])

            # Get the user we just saved. A bit clunky!
            self.fetched_users[flickr_user_id] = User.objects.get(nsid=flickr_user_id)

    def _fetch_photo_info(self, photo_id):
        """Calls the photos.getInfo() method of the Flickr API and returns the
        info about the photo.
        https://www.flickr.com/services/api/explore/flickr.photos.getInfo
        photo_id -- The Flickr photo ID.
        """
        try:
            results = self.api.photos.getInfo(photo_id=photo_id)
        except FlickrError as err:
            msg = f"Error when fetching photo info (photo {photo_id}): {err}"
            raise FetchError(msg) from err

        # Each tag on the photo is added by a specific Flickr user.
        # (Usually, but not always, the photo owner.)
        # Check that we've got info about that user in our DB.
        for tag in results["photo"]["tags"]["tag"]:
            self._fetch_user_if_missing(tag["author"])

        return results["photo"]

    def _fetch_photo_sizes(self, photo_id):
        """Calls the photos.getSizes() method of the Flickr API and returns the
        photo's sizes.
        https://www.flickr.com/services/api/explore/flickr.photos.getSizes
        photo_id -- The Flickr photo ID.
        """
        try:
            results = self.api.photos.getSizes(photo_id=photo_id)
        except FlickrError as err:
            msg = f"Error when fetching photo sizes (photo {photo_id}): {err}"
            raise FetchError(msg) from err
        return results["sizes"]

    def _fetch_photo_exif(self, photo_id):
        """Calls the photos.getExif() method of the Flickr API and returns the
        photo's EXIF data.
        https://www.flickr.com/services/api/explore/flickr.photos.getExif
        photo_id -- The Flickr photo ID.
        """
        try:
            results = self.api.photos.getExif(photo_id=photo_id)
        except FlickrError as err:
            msg = f"Error when fetching photo EXIF data (photo {photo_id}): {err}"
            raise FetchError(msg) from err
        return results["photo"]

    def _save_results(self):
        """Save all the data we've fetched about photos to the DB."""
        saver = PhotoSaver()
        for photo in self.results:
            saver.save_photo(photo)
        self.results_count += len(self.results)


class RecentPhotosFetcher(PhotosFetcher):
    """Fetches and saves data about an Account's recent Photos.

    By default ALL photos will be fetched.

    Supply a number of days to fetch() to restrict to the most recent days.
    """

    def __init__(self, account):
        super().__init__(account)

        # Maximum date of photos to return, if days or start are passed in:
        # By default, set it before Flickr so we get everything.
        self.min_date = datetime.datetime.strptime("2000-01-01", "%Y-%m-%d").astimezone(
            datetime.timezone.utc
        )

        # Maximum date of photos to return, if end is passed in:
        self.max_date = None

    def fetch(self, days=None, start=None, end=None):
        """Fetch all of the Account's user's photos, by default.
        days  - The number of days back to look, by upload date, or
                'all' to fetch all photos.
        start - The start date of a range in YYYY-MM-DD,YYYY-MM-DD format
        end   - The end date of a range in YYYY-MM-DD,YYYY-MM-DD format
        """

        if days and (start or end):
            msg = "You can't use --days with --start or --end"
            raise ValueError(msg)

        if days:
            try:
                self.min_date = datetime_now() - datetime.timedelta(days=days)
            except TypeError as err:
                if days != "all":
                    msg = "days should be an integer or 'all'."
                    raise FetchError(msg) from err
        elif start or end:
            try:
                if start:
                    self.min_date = datetime.datetime.strptime(
                        f"{start} 00:00:00", "%Y-%m-%d %H:%M:%S"
                    ).astimezone(datetime.timezone.utc)

                if end:
                    self.max_date = datetime.datetime.strptime(
                        f"{end} 23:59:59", "%Y-%m-%d %H:%M:%S"
                    ).astimezone(datetime.timezone.utc)

                if (start and end) and (start > end):
                    msg = "Start date must be before the end date."
                    raise ValueError(msg)

            except TypeError as err:
                msg = (
                    "Something went wrong with start or end. Please check the date "
                    "format. It should be YYYY-MM-DD"
                )
                raise FetchError(msg) from err
        else:
            msg = "Either set days or start and/or end."
            raise FetchError(msg)

        return super().fetch()

    def _call_api(self):
        """Fetch one page of results, containing very basic info about the
        Photos."""

        # Set up default arguments dictionary
        api_args = {
            "user_id": self.account.user.nsid,
            "per_page": self.items_per_page,
            "page": self.page_number,
        }

        if self.min_date:
            # Turn our datetime object into a unix timestamp and add to arguments:
            min_unixtime = calendar.timegm(self.min_date.timetuple())
            api_args["min_upload_date"] = min_unixtime

        if self.max_date:
            # Turn our datetime object into a unix timestamp and add to arguments:
            max_unixtime = calendar.timegm(self.max_date.timetuple())
            api_args["max_upload_date"] = max_unixtime

        try:
            results = self.api.people.getPhotos(**api_args)
        except FlickrError as err:
            msg = f"Error when fetching recent photos (page {self.page_number}: {err}"
            raise FetchError(msg) from err

        if (
            self.page_number == 1
            and "photos" in results
            and "pages" in results["photos"]
        ):
            # First time, set the total_pages there are to fetch.
            self.total_pages = int(results["photos"]["pages"])

        # Add the list of photos' data from this page on to our total list:
        self.results += results["photos"]["photo"]


class PhotosetsFetcher(Fetcher):
    def _call_api(self):
        """Fetch one page of results.

        https://www.flickr.com/services/api/flickr.photosets.getList.htm
        """

        try:
            results = self.api.photosets.getList(
                user_id=self.account.user.nsid,
                per_page=self.items_per_page,
                page=self.page_number,
            )
        except FlickrError as err:
            msg = f"Error when fetching photosets (page {self.page_number}): {err}"
            raise FetchError(msg) from err

        if (
            self.page_number == 1
            and "photosets" in results
            and "pages" in results["photosets"]
        ):
            # First time, set the total_pages there are to fetch.
            self.total_pages = int(results["photosets"]["pages"])

        # Add the list of photosets' data from this page on to our total list:
        self.results += results["photosets"]["photoset"]

    def _fetch_extra(self):
        """Before saving we need to get the list of photos in each photoset."""

        extra_results = []

        for _i, photoset in enumerate(self.results):
            photos = self._fetch_photos_in_photoset(photoset["id"])

            extra_results.append(
                {
                    "fetch_time": datetime_now(),
                    "photoset": photoset,
                    "photos": photos,
                    "user_obj": self.account.user,
                }
            )

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
        total_pages = 1  # Will get set to its proper value below.

        while page_number <= total_pages:
            try:
                results = self.api.photosets.getPhotos(
                    photoset_id=photoset_id,
                    user_id=self.account.user.nsid,
                    per_page=self.items_per_page,
                    page=page_number,
                )
            except FlickrError as err:
                msg = (
                    f"Error when fetching photos in photoset {photoset_id} "
                    f"(page {page_number}): {err}"
                )
                raise FetchError(msg) from err

            if "photoset" in results and "photo" in results["photoset"]:
                total_pages = results["photoset"]["pages"]
                photos += results["photoset"]["photo"]

            page_number += 1
            time.sleep(0.5)  # Being nice.

        return photos

    def _save_results(self):
        """Save all the data we've fetched about photosets to the DB."""
        saver = PhotosetSaver()
        for photoset in self.results:
            saver.save_photoset(photoset)
        self.results_count += len(self.results)
