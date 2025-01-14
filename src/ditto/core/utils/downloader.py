import contextlib
import os
import re
import shutil

import requests


class DownloadException(Exception):  # noqa: N818
    pass


class FileDownloader:
    """
    For downloading a file from a URL and saving it into /tmp/.

    Use like:
        from ditto.core.utils.downloader import filedownloader
        filepath = filedownloader.download(my_url, ['image/jpg'])

    filepath would be like '/tmp/image.jpg'
    """

    path = "/tmp/"

    def download(self, url, acceptable_content_types):
        """
        Downloads a file from a URL and saves it into /tmp/.
        Returns the filepath.

        Expects:
            url -- The URL of the file to fetch.
            acceptable_content_types -- A list of MIME types the request must
                match. eg:['image/jpeg', 'image/jpg', 'image/png', 'image/gif']

        Raises DownloadException if something goes wrong.
        """
        try:
            # From http://stackoverflow.com/a/13137873/250962
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                try:
                    if r.headers["Content-Type"] in acceptable_content_types:
                        # Where we'll temporarily save the file:
                        filename = self.make_filename(url, r.headers)
                        filepath = f"{self.path}{filename}"
                        # Save the file there:
                        with open(filepath, "wb") as f:
                            r.raw.decode_content = True
                            shutil.copyfileobj(r.raw, f)
                        return filepath

                    else:
                        msg = "Invalid content type ({}) when fetching {}".format(
                            r.headers["content_type"], url
                        )
                        raise DownloadException(msg)
                except KeyError as err:
                    msg = f"No content_type headers found when fetching {url}"
                    raise DownloadException(msg) from err
            else:
                msg = f"Got status code {r.status_code} when fetching {url}"
                raise DownloadException(msg)
        except requests.exceptions.RequestException as err:
            msg = f"Something when wrong when fetching {url}: {err}"
            raise DownloadException(msg) from err

    def make_filename(self, url, headers=None):
        """
        Find the filename of a downloaded file.
        Returns a string.

        url -- The URL of the file that's been downloaded.
        headers -- A dict of response headers from requesting the URL.

        url will probably end in something like 'filename.jpg'.
        If not, we'll try and use the filename from the Content-Disposition
        header.
        This is the case for Videos we download from Flickr.
        """
        headers = {} if headers is None else headers

        # Should work for photos:
        filename = os.path.basename(url)

        if filename == "":
            # Probably a Flickr video, so we have to get the filename from
            # headers:
            try:
                # Could be like 'attachment; filename=26897200312.avi'
                headers["Content-Disposition"]
                m = re.search(r"filename\=(.*?)$", headers["Content-Disposition"])
                with contextlib.suppress(AttributeError, IndexError):
                    filename = m.group(1)
            except KeyError:
                pass

        return filename


filedownloader = FileDownloader()
