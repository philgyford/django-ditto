import os

from django.core.files import File

from . import FetchError
from ..models import Photo
from ...core.utils.downloader import DownloadException, filedownloader


# A single class that fetches original photo/video files for existing
# Photo objects. Doesn't use the API.


class OriginalFilesFetcher(object):
    """
    Fetch the original photo files for a single Account.

    Not based off FlickrFetcher because we don't use the API so it's quite
    different. But still has a similar external appearance.

    Use something like:

        results = OriginalFilesFetcher(account=account_object).fetch()

    results is a dict that will have:
        'success': Boolean.
        'account': String. Indicating the Account (eg, its User's username).
        'fetched': Integer. If success, the number of files fetched, if any.
        'messages': List of strings. If no success, the failure message(s).
    """

    def __init__(self, account):
        self.account = None

        self.results = []

        self.results_count = 0

        self.return_value = {'fetched': 0}

        if account.user:
            self.return_value['account'] = account.user.username
        else:
            self.return_value['success'] = False
            self.return_value['messages'] = ['This account has no Flickr User']

        self.account = account

    def fetch(self, fetch_all=False):
        """
        Download and save original photos and videos for all Photo objects
        (or just those that don't already have them).

        self.account must be an Account object first.

        fetch_all -- Boolean. Fetch ALL photos/videos, even if we've already
                        got them?
        """
        # Might already have success=False from __init__():
        if 'success' not in self.return_value:
            self._fetch_files(fetch_all)

            self.return_value['fetched'] = self.results_count

        return self.return_value

    def _fetch_files(self, fetch_all):
        """
        Download and save original photos and videos for all Photo objects
        (or just those that don't already have them).

        fetch_all -- Boolean. Fetch ALL photos/videos, even if we've already
                        got them?
        """

        photos = Photo.objects.filter(user=self.account.user)

        if not fetch_all:
            photos = photos.filter(original_file='')

        error_messages = []

        for photo in photos:
            try:
                self._fetch_and_save_file(photo=photo, media_type='photo')
                self.results_count += 1
            except FetchError as e:
                error_messages.append(str(e))

            if photo.media == 'video':
                try:
                    self._fetch_and_save_file(photo=photo, media_type='video')
                    self.results_count += 1
                except FetchError as e:
                    error_messages.append(str(e))

        if len(error_messages) > 0:
            self.return_value['success'] = False
            self.return_value['messages'] = error_messages
        else:
            self.return_value['success'] = True

    def _fetch_and_save_file(self, photo, media_type):
        """
        Downloads a video or photo file and saves it to the Photo object.

        Expects:
            photo -- A Photo object.
            media_type -- String, either 'photo' or 'video'.

        Raises FetchError if something goes wrong.
        """

        if media_type == 'video':
            url = photo.remote_video_original_url
            # Accepted video formats:
            # https://help.yahoo.com/kb/flickr/sln15628.html
            # BUT, they all seem to be sent as video/mp4.
            acceptable_content_types = ['video/mp4',]

        else:
            url = photo.remote_original_url
            acceptable_content_types = [
                        'image/jpeg', 'image/jpg', 'image/png', 'image/gif',]

        filepath = False
        try:
            # Saves the file to /tmp/:
            filepath = filedownloader.download(url, acceptable_content_types)
        except DownloadException as e:
            raise FetchError(e)

        if filepath:
            # Reopen file and save to the Photo:
            reopened_file = open(filepath, 'rb')
            django_file = File(reopened_file)

            if media_type == 'video':
                photo.video_original_file.save(
                                    os.path.basename(filepath), django_file)
            else:
                photo.original_file.save(
                                    os.path.basename(filepath), django_file)


