# coding: utf-8
import os

try:
    from django.urls import reverse
except ImportError:
    # For Django 1.8
    from django.urls import reverse
from django.db import models
from django.templatetags.static import static

from imagekit.cachefiles import ImageCacheFile

from . import app_settings
from . import imagegenerators
from . import managers
from .utils import htmlify_description, htmlify_tweet
from ..core.models import DiffModelMixin, DittoItemModel, TimeStampedModelMixin

import json


class Account(TimeStampedModelMixin, models.Model):
    """The Twitter User Accounts with which we fetch data from the API.
    Each one is connected to a User object, so we only need to store API
    details here.
    """

    user = models.ForeignKey("User", blank=True, null=True, on_delete=models.SET_NULL)

    consumer_key = models.CharField(
        null=False,
        blank=True,
        max_length=255,
        help_text="(API Key) From https://apps.twitter.com",
    )
    consumer_secret = models.CharField(
        null=False, blank=True, max_length=255, help_text="(API Secret)"
    )
    access_token = models.CharField(null=False, blank=True, max_length=255)
    access_token_secret = models.CharField(null=False, blank=True, max_length=255)
    last_recent_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="The Twitter ID of the most recent Tweet fetched.",
    )
    last_favorite_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="The Twitter ID of the most recent favorited Tweet fetched.",
    )

    is_active = models.BooleanField(
        default=True,
        null=False,
        blank=False,
        help_text="If false, new Tweets won't be fetched.",
    )

    def save(self, *args, **kwargs):
        if self.user is None:
            self.updateUserFromTwitter()
            # Quietly ignoring errors. Sorry.
        super().save(*args, **kwargs)

    def __str__(self):
        if self.user:
            return str(self.user)
        else:
            return "%d" % self.pk

    class Meta:
        ordering = ["user__screen_name"]

    def get_absolute_url(self):
        if self.user:
            return reverse(
                "twitter:user_detail", kwargs={"screen_name": self.user.screen_name}
            )
        else:
            return ""

    def updateUserFromTwitter(self):
        """Calls the Twitter API to fetch the user details for this account.
        If the user object doesn't exist yet, it is created.
        But its relationship with this Account isn't saved here, only assigned.

        Returns:
        a) A dict, or
        b) False if we don't have API credentials.

        If a dict, will be like one of:
        {'account': 'text string', 'success': False, 'message': 'Error msg'}
        or
        {'account': 'text string', 'success': True, 'user': <User obj>}
        """
        from .fetch.fetch import FetchVerify

        if self.has_credentials():
            results = FetchVerify(account=self).fetch()
            if "user" in results and isinstance(results["user"], User):
                self.user = results["user"]
            return results
        else:
            return False

    def has_credentials(self):
        "Does this at least have something in its API fields? True or False"
        if (
            self.consumer_key
            and self.consumer_secret
            and self.access_token
            and self.access_token_secret
        ):
            return True
        else:
            return False


class Media(TimeStampedModelMixin, models.Model):
    """A photo, video or animated GIF attached to a Tweet.

    They have a bunch of common fields, and then some extra for Videos.
    A Tweet could have zero, one or more Medias. Yes that's the plural shut up.
    """

    # Mapping our internal names for sizes to the imagekit generators:
    IMAGE_SIZES = {
        "medium": {"generator": imagegenerators.Medium},
        "small": {"generator": imagegenerators.Small},
        "thumb": {"generator": imagegenerators.Thumbnail},
    }

    MEDIA_TYPES = (
        ("animated_gif", "Animated GIF"),
        ("photo", "Photo"),
        ("video", "Video"),
    )

    media_type = models.CharField(
        null=False, blank=False, max_length=12, choices=MEDIA_TYPES
    )

    # A media item can belong to more than one tweet. Why?
    # Because if tweet 1 retweets tweet 2, which has a photo, then we save
    # that photo as attached to both tweets 1 and 2.
    # Because that's how the API does it too.
    tweets = models.ManyToManyField("Tweet", related_name="media")

    twitter_id = models.BigIntegerField(null=False, blank=False, unique=True)
    image_url = models.URLField(
        null=False, blank=False, help_text="URL of the image itself on Twitter.com"
    )

    large_w = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Large width"
    )
    large_h = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Large height"
    )
    medium_w = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Medium width"
    )
    medium_h = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Medium height"
    )
    small_w = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Small width"
    )
    small_h = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Small height"
    )
    thumb_w = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Thumbnail width"
    )
    thumb_h = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Thumbnail height"
    )

    # START VIDEO-ONLY PROPERTIES.

    # These will be in order from lowest bitrate to highest.
    mp4_url = models.URLField(
        null=False, blank=True, verbose_name="MP4 URL", help_text="For Animated GIFs"
    )
    dash_url = models.URLField(
        null=False, blank=True, verbose_name="MPEG-DASH URL (.mpd, streaming)"
    )
    xmpeg_url = models.URLField(
        null=False, blank=True, verbose_name="X-MPEG URL (HLS, .m3u8, streaming"
    )

    aspect_ratio = models.CharField(
        null=False, blank=True, max_length=21, help_text='eg, "4:3" or "16:9"'
    )
    duration = models.PositiveIntegerField(
        null=True, blank=True, help_text="In milliseconds"
    )
    # END VIDEO-ONLY PROPERTIES

    def upload_path(self, filename):
        "Make path under MEDIA_ROOT where original files will be saved."

        # eg get '12345678' from '12345678.jpg':
        name = os.path.splitext(filename)[0]

        # If filename is '12345678.jpg':
        # 'twitter/media/56/78/12345678.jpg'
        return "/".join(
            [app_settings.TWITTER_DIR_BASE, "media", name[-4:-2], name[-2:], filename]
        )

    image_file = models.ImageField(
        upload_to=upload_path, null=False, blank=True, default=""
    )
    mp4_file = models.FileField(
        upload_to=upload_path,
        null=False,
        blank=True,
        default="",
        help_text="Only used for Animated GIFs",
    )

    # All Items (eg, used in Admin):
    objects = models.Manager()

    # There is no Public manager for media, as we don't have the concept of
    # private/public Media items.

    def __str__(self):
        return "%s %d" % (self.get_media_type_display(), self.id)

    class Meta:
        ordering = ["time_created"]
        verbose_name = "Media item"
        verbose_name_plural = "Media items"

    @property
    def thumbnail_w(self):
        "Because we usually actually want 150, not whatever thumb_w is."
        return 150

    @property
    def thumbnail_h(self):
        "Because we usually actually want 150, not whatever thumb_h is."
        return 150

    @property
    def large_url(self):
        "URL to local or remote original-size image."
        return self._image_url("large")

    @property
    def medium_url(self):
        "URL to local or remote image, maximum 1200px high/wide."
        return self._image_url("medium")

    @property
    def small_url(self):
        "URL to local or remote image, maximum 680px high/wide."
        return self._image_url("small")

    @property
    def thumb_url(self):
        "URL to local or remote image, 150px square."
        return self._image_url("thumb")

    @property
    def thumbnail_url(self):
        "URL to local or remote image, 150px square. For consistency."
        return self.thumb_url

    @property
    def video_url(self):
        """
        The URL to our preferred video source.
        Depends on if we're hosting video locally or on twitter.com, what
        kind of thing this is (GIF or video), and what URLs we have.
        Returns a URL or an empty string.
        """
        url = ""
        video_type = self._video_type()

        if video_type is not None:
            if video_type[1] == "local":
                if video_type[0] == "mp4":
                    return self.mp4_file.url
            else:
                if video_type[0] == "mp4":
                    url = self.mp4_url
                elif video_type[0] == "xmpeg":
                    url = self.xmpeg_url
                elif video_type[0] == "dash":
                    url = self.dash_url

        return url

    @property
    def video_mime_type(self):
        """
        The MIME type for our preferred video URL.
        Returns a mime type or an empty string.
        """
        mime_type = ""
        video_type = self._video_type()

        if video_type is not None:
            if video_type[0] == "mp4":
                mime_type = "video/mp4"
            elif video_type[0] == "xmpeg":
                mime_type = "application/x-mpegURL"
            elif video_type[0] == "dash":
                mime_type = "application/dash+xml"

        return mime_type

    def _image_url(self, size):
        """
        Helper for the self.*_url() property methods.
        size -- one of 'large', 'medium', 'small', or 'thumbnail'.
        """
        if app_settings.TWITTER_USE_LOCAL_MEDIA:
            return self._local_image_url(size)
        else:
            return self._remote_image_url(size)

    def _local_image_url(self, size):
        """
        Generate the URL of an image of a particular size, hosted locally,
        based on the original file (which must already be downloaded).
        size -- one of 'large', 'medium', 'small', or 'thumbnail'.
        """
        if self.image_file:
            if size == "large":
                # Essentially the original file.
                return self.image_file.url
            else:
                generator = self.IMAGE_SIZES[size]["generator"]
                try:
                    image_generator = generator(source=self.image_file)
                    result = ImageCacheFile(image_generator)
                    return result.url
                except Exception:
                    # We have an original file but something's wrong with it.
                    # Might be 0 bytes or something.
                    return static("ditto-core/img/original_error.jpg")
        else:
            # We haven't downloaded an original file for this.
            return static("ditto-core/img/original_missing.jpg")

    def _remote_image_url(self, size):
        """
        Generate the URL of an image of a particular size, at Twitter.
        size -- one of 'large', 'medium', 'small', or 'thumbnail'.
        """
        return "%s:%s" % (self.image_url, size)

    def _video_type(self):
        """
        Which video type should we use for this item?
        Returns None or a tuple of type and 'remote'/'local',
        eg: ('xmpeg', 'remote') or ('mp4', 'local')
        """
        if app_settings.TWITTER_USE_LOCAL_MEDIA:
            return self._local_video_type()
        else:
            return self._remote_video_type()

    def _local_video_type(self):
        """
        When hosting media locally, which video type should we use for this?
        Returns None or a tuple of type and 'remote'/'local',
        eg: ('xmpeg', 'remote') or ('mp4', 'local')
        """
        if self.media_type == "animated_gif" and self.mp4_file:
            return ("mp4", "local")
        else:
            # We can't currently save video files except MP4s for animated
            # gifs, so try to fall back to the remote URLs.
            return self._remote_video_type()

    def _remote_video_type(self):
        """
        When hosting media remotely, which video type should we use for this?
        Returns None or a tuple of type and 'remote'/'local',
        eg: ('xmpeg', 'remote') or ('mp4', 'local')
        """
        video_type = None
        if self.media_type == "video":
            # Prefer the streaming URL over MP4:
            if self.xmpeg_url:
                video_type = ("xmpeg", "remote")
            elif self.mp4_url:
                video_type = ("mp4", "remote")
            elif self.dash_url:
                video_type = ("dash", "remote")

        elif self.media_type == "animated_gif" and self.mp4_url:
            video_type = ("mp4", "remote")

        return video_type


class ExtraTweetManagers(models.Model):
    """Managers to use in the Tweet model, in addition to the defaults defined
    in DittoItemModel.
    These need to be here, rather than in the Tweet model, or they will
    override those in DittoItemModel.
    """

    # For Tweets favorited by any Account:
    favorite_objects = managers.FavoritesManager()
    public_favorite_objects = managers.PublicFavoritesManager()

    tweet_objects = managers.TweetsManager()
    public_tweet_objects = managers.PublicTweetsManager()

    class Meta:
        abstract = True


class Tweet(DittoItemModel, ExtraTweetManagers):
    """We don't replicate all of the possible Tweet attributes here, only
    enough to display the most useful things. Given we save the raw JSON
    about this tweet, we could add more attributes in future, even if original
    tweets are deleted on Twitter.

    Also, we don't include any 'perspectival' attributes - ones that will vary
    depending on which Account fetched this data. eg, `favorited` or
    `current_user_retweet`.
    """

    ditto_item_name = "twitter_tweet"

    # Properties inherited from DittoItemModel:
    #
    # title         (CharField)
    # permalink     (URLField)
    # summary       (CharField)
    # is_private    (BooleanField)
    # fetch_time    (DateTimeField, UTC)
    # post_time     (DateTimeField, UTC)
    # latitude      (DecimalField)
    # longitude     (DecimalField)
    # raw           (TextField)

    user = models.ForeignKey("User", on_delete=models.CASCADE)

    text = models.TextField(null=False, blank=False)
    text_html = models.TextField(
        null=False, blank=True, help_text="An HTMLified version of the Tweet's text"
    )
    twitter_id = models.BigIntegerField(
        null=False, blank=False, unique=True, db_index=True
    )

    # Favorite and Retweet Count not present in tweets ingested from a
    # downloaded archive, hence null=True:
    favorite_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Approximately how many times this had been favorited when fetched",
    )
    retweet_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of times this had been retweeted when fetched",
    )

    in_reply_to_screen_name = models.CharField(
        null=False,
        blank=True,
        max_length=20,
        help_text="Screen name of the original Tweet's author, if this is a reply",
    )
    in_reply_to_status_id = models.BigIntegerField(
        null=True, blank=True, help_text="The ID of the Tweet replied to, if any"
    )
    in_reply_to_user_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID of the original Tweet's author, if this is a reply",
    )

    language = models.CharField(
        null=False,
        blank=False,
        default="und",
        max_length=20,
        help_text="A BCP 47 language identifier, or 'und' if it couldn't be detected",
    )

    # Just enough of the place data to display something readable and useful:
    place_attribute_street_address = models.CharField(
        null=False, blank=True, max_length=255
    )
    place_full_name = models.CharField(null=False, blank=True, max_length=255)
    place_country = models.CharField(null=False, blank=True, max_length=255)

    quoted_status_id = models.BigIntegerField(
        null=True, blank=True, help_text="The ID of the Tweet quoted, if any"
    )

    retweeted_status_id = models.BigIntegerField(
        null=True, blank=True, help_text="The ID of the retweeted Tweet, if any"
    )

    source = models.CharField(
        null=False,
        blank=True,
        max_length=255,
        help_text="Utility used to post the Tweet",
    )
    media_count = models.PositiveSmallIntegerField(
        null=False,
        blank=True,
        default=0,
        help_text="Number of Photos/Videos attached to this Tweet",
    )

    def __str__(self):
        return self.title

    class Meta:
        # It's possible to have tweets posted in the same second that
        # need to be then ordered by twitter_id:
        ordering = ["-post_time", "-twitter_id"]
        # So that the ordering is faster:
        indexes = [
            # Speeds up the COUNT(*) query on daily pages:
            models.Index(fields=["user", "post_time", "is_private"]),
        ]

    def save(self, *args, **kwargs):
        "Privacy depends on the user, so ensure it's set correctly"
        self.is_private = self.user.is_private
        self.make_text_html()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "twitter:tweet_detail",
            kwargs={
                "screen_name": self.user.screen_name,
                "twitter_id": self.twitter_id,
            },
        )

    def get_next_public_by_post_time(self):
        "Next Tweet by this User, if they're public."
        try:
            return (
                Tweet.public_tweet_objects.filter(
                    post_time__gte=self.post_time, user=self.user
                )
                .exclude(pk=self.pk)
                .order_by("post_time")[:1]
                .get()
            )
        except Exception:
            pass

    def get_previous_public_by_post_time(self):
        "Previous Tweet by this User, if they're public."
        try:
            return (
                Tweet.public_tweet_objects.filter(
                    post_time__lte=self.post_time, user=self.user
                )
                .exclude(pk=self.pk)
                .order_by("-post_time")[:1]
                .get()
            )
        except Exception:
            pass

    # Shortcuts:
    def get_next(self):
        return self.get_next_public_by_post_time()

    def get_previous(self):
        return self.get_previous_public_by_post_time()

    @property
    def is_reply(self):
        if self.in_reply_to_screen_name == "":
            return False
        else:
            return True

    @property
    def in_reply_to_url(self):
        "If it's a reply, the link to the tweet replied to."
        if self.is_reply:
            return "https://twitter.com/%s/status/%s" % (
                self.in_reply_to_screen_name,
                self.in_reply_to_status_id,
            )
        else:
            return ""

    @property
    def place(self):
        return ", ".join(
            filter(
                None,
                (
                    self.place_attribute_street_address,
                    self.place_full_name,
                    self.place_country,
                ),
            )
        )

    @property
    def account(self):
        "The Account whose tweet this is, if any. Otherwise, None."
        try:
            return self.user.account_set.all()[0]
        except IndexError:
            return None

    def make_text_html(self):
        """Uses the raw JSON for the tweet to set self.text_html to a nice
        HTML version of the tweet.
        """
        try:
            json_data = json.loads(self.raw)
        except ValueError:
            return False
        self.text_html = htmlify_tweet(json_data)
        return True

    def get_quoted_tweet(self):
        # There's one we saved earlier, so use that.
        if hasattr(self, "_quoted_tweet"):
            return self._quoted_tweet

        tweet = None
        if self.quoted_status_id:
            try:
                tweet = Tweet.public_objects.get(twitter_id=self.quoted_status_id)
            except Tweet.DoesNotExist:
                pass

        # Save for later:
        self._quoted_tweet = tweet
        return tweet

    def get_retweeted_tweet(self):
        # There's one we saved earlier, so use that.
        if hasattr(self, "_retweeted_tweet"):
            return self._retweeted_tweet

        tweet = None
        if self.retweeted_status_id:
            try:
                tweet = Tweet.public_objects.get(twitter_id=self.retweeted_status_id)
            except Tweet.DoesNotExist:
                pass

        # Save for later:
        self._retweeted_tweet = tweet
        return tweet

    def _summary_source(self):
        "Used to make the `summary` property."
        return self.title


class User(TimeStampedModelMixin, DiffModelMixin, models.Model):
    """A Twitter user.
    We don't replicate all of the possible User attributes here, only enough
    to display the most useful things.
    """

    twitter_id = models.BigIntegerField(null=False, blank=False, unique=True)
    screen_name = models.CharField(
        null=False, blank=False, max_length=20, help_text="Username, eg, 'samuelpepys'"
    )
    name = models.CharField(
        null=False, blank=False, max_length=50, help_text="eg, 'Samuel Pepys'"
    )
    url = models.URLField(
        null=False,
        blank=True,
        default="",
        max_length=255,
        help_text="A URL provided by the user as part of their profile",
    )
    # Inverse of Twitter's 'protected', to be similar to DittoItemModel:
    is_private = models.BooleanField(
        null=False, default=False, help_text="True if this user is 'protected'"
    )
    is_verified = models.BooleanField(null=False, default=False)

    # User data in ingested archives don't have this:
    created_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="UTC time when this account was created on Twitter",
    )

    description = models.CharField(null=False, blank=True, max_length=255)
    description_html = models.TextField(
        null=False,
        blank=True,
        help_text="An HTMLified version of the User's description",
    )
    location = models.CharField(null=False, blank=True, max_length=255)
    time_zone = models.CharField(null=False, blank=True, max_length=255)

    profile_image_url_https = models.URLField(null=False, blank=True, max_length=255)

    # This is how it's spelt in the API:
    favourites_count = models.PositiveIntegerField(
        null=False,
        blank=False,
        default=0,
        help_text=(
            "The number of tweets this user has favorited in " "the account’s lifetime"
        ),
    )
    followers_count = models.PositiveIntegerField(
        null=False,
        blank=False,
        default=0,
        help_text="The number of followers this account has",
    )
    friends_count = models.PositiveIntegerField(
        null=False,
        blank=False,
        default=0,
        help_text="Tne number of users this account is following.",
    )
    listed_count = models.PositiveIntegerField(
        null=False,
        blank=False,
        default=0,
        help_text="The number of public lists this user is a member of",
    )
    statuses_count = models.PositiveIntegerField(
        null=False,
        blank=False,
        default=0,
        help_text="The number of tweets, including retweets, by this user",
    )

    # As on DittoItemModel:
    fetch_time = models.DateTimeField(
        null=True, blank=True, help_text="The time the data was last fetched."
    )
    raw = models.TextField(
        null=False, blank=True, help_text="eg, the raw JSON from the API."
    )

    def avatar_upload_path(self, filename):
        """
        Make path under MEDIA_ROOT where avatar file will be saved.

        eg, if twitter_id is 12345678:
            twitter/avatars/56/78/12345678/avatar_name.jpg
        """

        # We can't just join all these parts in one go, because if the ID
        # isn't long enough to have two numbered directories, (ie, it's only
        # 1 or 2 digits) then Django 1.8 creates a path with '//' rather than
        # just ignoring that directory.

        # So this is a bit laborious:

        # 'twitter/avatars':
        start = "/".join([app_settings.TWITTER_DIR_BASE, "avatars"])
        # '/78/12345678/avatar_name.jpg':
        end = "/".join([str(self.twitter_id)[-2:], str(self.twitter_id), str(filename)])
        # The bit that will be empty for 1-2 digit IDs:
        # '56':
        middle = str(self.twitter_id)[-4:-2]

        if middle:
            return "/".join([start, middle, end])
        else:
            return "/".join([start, end])

    avatar = models.ImageField(
        upload_to=avatar_upload_path, null=False, blank=True, default=""
    )

    favorites = models.ManyToManyField(Tweet, related_name="favoriting_users")

    objects = models.Manager()
    # All Users that have Accounts:
    objects_with_accounts = managers.WithAccountsManager()

    def __str__(self):
        return "@%s" % self.screen_name

    class Meta:
        ordering = ["screen_name"]

    def save(self, *args, **kwargs):
        """If the user's privacy status has changed, we need to change the
        privacy of all their tweets
        And we also HTMLify their description.
        """
        if self.get_field_diff("is_private") is not None:
            Tweet.objects.filter(user=self).update(is_private=self.is_private)
        self.make_description_html()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("twitter:user_detail", kwargs={"screen_name": self.screen_name})

    def make_description_html(self):
        """Uses the raw JSON for the user to set self.description_html to a nice
        HTML version of the description.
        """
        try:
            json_data = json.loads(self.raw)
        except ValueError:
            return False
        self.description_html = htmlify_description(json_data)
        return True

    @property
    def permalink(self):
        return "https://twitter.com/%s" % self.screen_name

    @property
    def avatar_url(self):
        try:
            return self.avatar.url
        except ValueError:
            return static("ditto-core/img/default_avatar.png")

    @property
    def profile_image_url(self):
        return self.profile_image_url_https

    @property
    def favorites_count(self):
        return self.favourites_count
