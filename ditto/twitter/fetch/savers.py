import datetime
import json
import os
import pytz

from django.conf import settings
from django.core.files import File

from ..models import Media, Tweet, User
from ...core.utils import truncate_string
from ...core.utils.downloader import DownloadException, filedownloader

# Classes that take JSON data from the Twitter API and create or update
# objects.
#
# They don't call the API at all. But UserSaver fetches avatar images.

# CLASSES HERE:
#
# SaveUtilsMixin
# UserSaver
# TweetSaver


class SaveUtilsMixin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _api_time_to_datetime(self, api_time, time_format="%a %b %d %H:%M:%S +0000 %Y"):
        """Change a text datetime from the API to a datetime with timezone.
        api_time is a string like 'Wed Nov 15 16:55:59 +0000 2006'.
        """
        return datetime.datetime.strptime(api_time, time_format).replace(
            tzinfo=pytz.utc
        )


class UserSaver(SaveUtilsMixin, object):
    "Provides a method for creating/updating a User using data from the API."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_user(self, user, fetch_time, download_avatar=True):
        """With Twitter user data from the API, it creates or updates the User
        and returns the User object.

        Keyword arguments:
        user -- A dict of the data about a user from the API's JSON.
        fetch_time -- A datetime.
        download_avatar -- Boolean. Should user's profile pic be downloaded?

        Returns the User object.
        """
        raw_json = json.dumps(user)

        defaults = {
            "fetch_time": fetch_time,
            "raw": raw_json,
            "screen_name": user["screen_name"],
            "name": user["name"],
            "is_private": user["protected"],
            "is_verified": user["verified"],
            "profile_image_url_https": user["profile_image_url_https"],
        }

        # When ingesting tweets there are lots of fields the 'user' element
        # doesn't have, compared to the API:

        if "created_at" in user:
            defaults["created_at"] = self._api_time_to_datetime(user["created_at"])

        # If there's a URL it will be a t.co shortened one.
        # So we go through the entities to find its expanded version.
        if "url" in user and user["url"]:
            user_url = user["url"]
            if "url" in user["entities"] and "urls" in user["entities"]["url"]:
                for url_dict in user["entities"]["url"]["urls"]:
                    if (
                        url_dict["url"] == user["url"]
                        and url_dict["expanded_url"] is not None
                    ):
                        user_url = url_dict["expanded_url"]
            defaults["url"] = user_url

        if "description" in user:
            defaults["description"] = user["description"] if user["description"] else ""

        if "location" in user:
            defaults["location"] = user["location"] if user["location"] else ""

        if "time_zone" in user:
            defaults["time_zone"] = user["time_zone"] if user["time_zone"] else ""

        if "favourites_count" in user:
            defaults["favourites_count"] = user["favourites_count"]

        for a_count in [
            "followers_count",
            "friends_count",
            "listed_count",
            "statuses_count",
        ]:
            if a_count in user:
                defaults[a_count] = user[a_count]

        user_obj, created = User.objects.update_or_create(
            twitter_id=user["id"], defaults=defaults
        )

        if download_avatar:
            user_obj = self._fetch_and_save_avatar(user_obj)

        return user_obj

    def _fetch_and_save_avatar(self, user):
        """
        Download and save the Avatar/profile pic for this user.
        If the user's profile_image_url_https property doesn't match an image
        we've already downloaded for them, we fetch and save it.

        user -- User object.
        """
        filename = os.path.basename(user.profile_image_url_https)
        # Where we'd save the user's avatar image to:
        avatar_upload_path = os.path.join(
            settings.MEDIA_ROOT, user.avatar_upload_path(filename)
        )
        if os.path.exists(avatar_upload_path):
            return user

        # We don't have this image yet, so fetch and save it.
        try:
            avatar_filepath = filedownloader.download(
                user.profile_image_url_https,
                ["image/jpeg", "image/jpg", "image/png", "image/gif"],
            )

            user.avatar.save(
                os.path.basename(avatar_filepath), File(open(avatar_filepath, "rb"))
            )
        except DownloadException:
            pass

        return user


class TweetSaver(SaveUtilsMixin, object):
    """Provides a method for creating/updating a Tweet (and its User) using
    data from the API. Also used by ingest.TweetIngester()
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_media(self, tweet):
        """Takes a Tweet object and creates or updates any photos and videos
        based on the JSON data in its `raw` field.

        Keyword arguments:
        tweet -- The Tweet object. Must have been saved as we need its id.

        Returns:
        Total number of items for this Tweet (regardless of whether they were
            created or updated).
        """
        import itertools

        # What we'll return:
        media_count = 0

        try:
            json_data = json.loads(tweet.raw)
        except ValueError:
            return media_count

        try:
            media = json_data["extended_entities"]["media"]
        except KeyError:
            return media_count

        for item in media:
            # Things common to photos, animated GIFs and videos.

            defaults = {
                "media_type": "photo",
                "twitter_id": item["id"],
                "image_url": item["media_url_https"],
            }

            valid_types = [type for type, name in Media.MEDIA_TYPES]

            if item["type"] in valid_types:
                defaults["media_type"] = item["type"]

            for size in ["large", "medium", "small", "thumb"]:
                if size in item["sizes"]:
                    defaults[size + "_w"] = item["sizes"][size]["w"]
                    defaults[size + "_h"] = item["sizes"][size]["h"]
                else:
                    defaults[size + "_w"] = None
                    defaults[size + "_h"] = None

            # Adding things ony used for videos and animated GIFs:
            if "video_info" in item:

                info = item["video_info"]

                # eg, '16:9'
                defaults["aspect_ratio"] = "%s:%s" % (
                    info["aspect_ratio"][0],
                    info["aspect_ratio"][1],
                )

                if "duration_millis" in info:
                    defaults["duration"] = info["duration_millis"]

                # Group the variants into a dict with keys like 'video/mp4'
                # and values being a list of dicts. Each of those dicts
                # being a single variant.
                # [
                #   {'video/mp4': [{'url':'...', 'bitrate':320000},
                #                  {'url':'...', 'bitrate':832000},]
                #   },
                # ]
                # A bit less necessary now that mp4s are deprecated for videos.
                # (But there's still a single(?) mp4 url for animated GIFs.)

                # Sort the list of dicts by 'content_type'.
                # Need to do this for the next grouping stage.
                sorted_variants = sorted(
                    info["variants"], key=lambda k: k["content_type"]
                )
                grouped_variants = {}

                for key, variants in itertools.groupby(
                    sorted_variants, lambda k: k["content_type"]
                ):
                    grouped_variants[key] = list(variants)

                if "application/dash+xml" in grouped_variants:
                    defaults["dash_url"] = grouped_variants["application/dash+xml"][0][
                        "url"
                    ]
                if "application/x-mpegURL" in grouped_variants:
                    defaults["xmpeg_url"] = grouped_variants["application/x-mpegURL"][
                        0
                    ]["url"]

                if (
                    defaults["media_type"] == "animated_gif"
                    and "video/mp4" in grouped_variants
                ):
                    # Only Animated GIFs have mp4s now.
                    # https://twittercommunity.com/t/retiring-mp4-video-output/66093
                    defaults["mp4_url"] = grouped_variants["video/mp4"][0]["url"]

            media_obj, created = Media.objects.update_or_create(
                twitter_id=item["id"], defaults=defaults
            )
            media_count += 1

            if tweet not in media_obj.tweets.all():
                media_obj.tweets.add(tweet)

        return media_count

    def save_tweet(self, tweet, fetch_time):
        """Takes a dict of tweet data from the API and creates or updates a
        Tweet object and its associated User object.

        Keyword arguments:
        tweet -- The tweet data.
        fetch_time -- A datetime.

        Returns:
        The Tweet object that was created or updated.
        """
        raw_json = json.dumps(tweet)
        try:
            created_at = self._api_time_to_datetime(tweet["created_at"])
        except ValueError:
            # Because the tweets imported from a downloaded archive have a
            # different format for created_at. Of course. Why not?!
            created_at = self._api_time_to_datetime(
                tweet["created_at"], time_format="%Y-%m-%d %H:%M:%S +0000"
            )

        user = UserSaver().save_user(tweet["user"], fetch_time)

        if "full_text" in tweet:
            # For new (2016) 'extended' format tweet data.
            # https://dev.twitter.com/overview/api/upcoming-changes-to-tweets
            text = tweet["full_text"]
            # Cuts off any @usernames at the start and a trailing URL at the end:
            frm = tweet["display_text_range"][0]
            to = tweet["display_text_range"][1]
            title = text[frm:to]
        else:
            # Older 'classic' format tweet data.
            text = tweet["text"]
            title = text

        # titles can only be 255 characters
        title = truncate_string(
            title, strip_html=True, chars=255, truncate=u"…", at_word_boundary=True
        )

        defaults = {
            "fetch_time": fetch_time,
            "raw": raw_json,
            "user": user,
            "is_private": user.is_private,
            "post_time": created_at,
            "permalink": "https://twitter.com/%s/status/%s"
            % (user.screen_name, tweet["id"]),
            "title": title.replace("\n", " ").replace("\r", " "),
            "text": text,
            "twitter_id": tweet["id"],
            "source": tweet["source"],
        }

        # Some of these are only present in tweets from the API (not in the
        # tweets from the downloaded archive).
        # Some are just not always present, such as coordinates and place stuff.

        if "favorite_count" in tweet:
            defaults["favorite_count"] = tweet["favorite_count"]

        if "retweet_count" in tweet:
            defaults["retweet_count"] = tweet["retweet_count"]

        if "lang" in tweet:
            defaults["language"] = tweet["lang"]

        if (
            "coordinates" in tweet
            and tweet["coordinates"]
            and "type" in tweet["coordinates"]
        ):
            if tweet["coordinates"]["type"] == "Point":
                defaults["latitude"] = tweet["coordinates"]["coordinates"][1]
                defaults["longitude"] = tweet["coordinates"]["coordinates"][0]
            # TODO: Handle Polygons?

        if "in_reply_to_screen_name" in tweet and tweet["in_reply_to_screen_name"]:
            defaults["in_reply_to_screen_name"] = tweet["in_reply_to_screen_name"]
        else:
            defaults["in_reply_to_screen_name"] = ""

        if "in_reply_to_status_id" in tweet:
            defaults["in_reply_to_status_id"] = tweet["in_reply_to_status_id"]

        if "in_reply_to_user_id" in tweet:
            defaults["in_reply_to_user_id"] = tweet["in_reply_to_user_id"]

        if "place" in tweet and tweet["place"] is not None:
            if (
                "attributes" in tweet["place"]
                and "street_address" in tweet["place"]["attributes"]
            ):
                defaults["place_attribute_street_address"] = tweet["place"][
                    "attributes"
                ]["street_address"]
            if "full_name" in tweet["place"]:
                defaults["place_full_name"] = tweet["place"]["full_name"]
            if "country" in tweet["place"]:
                defaults["place_country"] = tweet["place"]["country"]

        if "quoted_status_id" in tweet:
            defaults["quoted_status_id"] = tweet["quoted_status_id"]

            if "quoted_status" in tweet:
                # If tweet 1 quotes tweet 2 that quotes tweet 3, then
                # tweet 2 will have 'quoted_status_id' but not 'quoted_status'.
                # But the tweet does have quoted_status, we'll create/update
                # the quoted User object, and quoted Tweet.
                UserSaver().save_user(
                    tweet["quoted_status"]["user"], fetch_time
                )
                self.save_tweet(tweet["quoted_status"], fetch_time)

        if "retweeted_status" in tweet:
            defaults["retweeted_status_id"] = tweet["retweeted_status"]["id"]

            UserSaver().save_user(
                tweet["retweeted_status"]["user"], fetch_time
            )
            self.save_tweet(tweet["retweeted_status"], fetch_time)

        tweet_obj, created = Tweet.objects.update_or_create(
            twitter_id=tweet["id"], defaults=defaults
        )

        # Create/update any Photos, and update the Tweet's photo_count:
        media_count = self.save_media(tweet=tweet_obj)
        tweet_obj.media_count = media_count

        tweet_obj.save()

        return tweet_obj
