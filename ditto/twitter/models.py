# coding: utf-8
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.templatetags.static import static

from . import managers
from .utils import htmlify_description, htmlify_tweet
from ..core.managers import PublicItemManager
from ..core.models import DiffModelMixin, DittoItemModel, TimeStampedModelMixin

import json


class Account(TimeStampedModelMixin, models.Model):
    """The Twitter User Accounts with which we fetch data from the API.
    Each one is connected to a User object, so we only need to store API
    details here.
    """

    user = models.ForeignKey('User', blank=True, null=True,
                                                    on_delete=models.SET_NULL)

    consumer_key = models.CharField(null=False, blank=True, max_length=255,
            help_text="(API Key) From https://apps.twitter.com")
    consumer_secret = models.CharField(null=False, blank=True, max_length=255,
            help_text="(API Secret)")
    access_token = models.CharField(null=False, blank=True, max_length=255)
    access_token_secret = models.CharField(null=False, blank=True,
                                                                max_length=255)
    last_recent_id = models.BigIntegerField(null=True, blank=True,
            help_text="The Twitter ID of the most recent Tweet fetched.")
    last_favorite_id = models.BigIntegerField(null=True, blank=True,
            help_text="The Twitter ID of the most recent favorited Tweet fetched.")

    is_active = models.BooleanField(default=True, null=False, blank=False,
                        help_text="If false, new Tweets won't be fetched.")

    def save(self, *args, **kwargs):
        if self.user is None:
            result = self.updateUserFromTwitter()
            # Quietly ignoring errors. Sorry.
        super().save(*args, **kwargs)

    def __str__(self):
        if self.user:
            return str(self.user)
        else:
            return '%d' % self.pk

    class Meta:
        ordering = ['user__screen_name']

    def get_absolute_url(self):
        if self.user:
            return reverse('twitter:user_detail',
                        kwargs={'screen_name': self.user.screen_name})
        else:
            return ''

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
            if 'user' in results and isinstance(results['user'], User):
                self.user = results['user']
            return results
        else:
            return False

    def has_credentials(self):
        "Does this at least have something in its API fields? True or False"
        if self.consumer_key and self.consumer_secret and self.access_token and self.access_token_secret:
            return True
        else:
            return False


class Media(TimeStampedModelMixin, models.Model):
    """Photos and Videos.

    They have a bunch of common fields, and then some extra for Videos.
    A Tweet could have zero, one or more Medias. Yes that's the plural shut up.
    """
    MEDIA_TYPES = (
        ('animated_gif', 'Animated GIF'),
        ('photo', 'Photo'),
        ('video', 'Video'),
    )

    media_type = models.CharField(null=False, blank=False, max_length=8,
                                                        choices=MEDIA_TYPES)

    tweet = models.ForeignKey('Tweet')
    twitter_id = models.BigIntegerField(null=False, blank=False, unique=True)
    image_url = models.URLField(null=False, blank=False,
                                        help_text="URL of the image itself")

    is_private = models.BooleanField(default=False, null=False, blank=False,
        help_text="If true, this item will not be shown on public-facing pages.")

    large_w = models.PositiveSmallIntegerField(null=True, blank=True,
                                                verbose_name="Large width")
    large_h = models.PositiveSmallIntegerField(null=True, blank=True,
                                                verbose_name="Large height")
    medium_w = models.PositiveSmallIntegerField(null=True, blank=True,
                                                verbose_name="Medium width")
    medium_h = models.PositiveSmallIntegerField(null=True, blank=True,
                                                verbose_name="Medium height")
    small_w = models.PositiveSmallIntegerField(null=True, blank=True,
                                                verbose_name="Small width")
    small_h = models.PositiveSmallIntegerField(null=True, blank=True,
                                                verbose_name="Small height")
    thumb_w = models.PositiveSmallIntegerField(null=True, blank=True,
                                                verbose_name="Thumbnail width")
    thumb_h = models.PositiveSmallIntegerField(null=True, blank=True,
                                                verbose_name="Thumbnail height")

    # START VIDEO-ONLY PROPERTIES.

    # These will be in order from lowest bitrate to highest.
    mp4_url = models.URLField(null=False, blank=True,
                        verbose_name='MP4 URL', help_text="For Animated GIFs")
    dash_url = models.URLField(null=False, blank=True,
                                                verbose_name='MPEG-DASH URL')
    xmpeg_url = models.URLField(null=False, blank=True,
                                                    verbose_name='X-MPEG URL')

    aspect_ratio = models.CharField(null=False, blank=True, max_length=5,
                                            help_text='eg, "4:3" or "16:9"')
    duration = models.PositiveIntegerField(null=True, blank=True,
                                                help_text="In milliseconds")
    # END VIDEO-ONLY PROPERTIES


    # All Items (eg, used in Admin):
    objects = models.Manager()

    # All Items which aren't private. Should ALWAYS be used for public pages:
    public_objects = PublicItemManager()

    def __str__(self):
        return '%s %d' % (self.get_media_type_display(), self.id)

    class Meta:
        ordering = ['time_created']
        verbose_name = 'Media item'
        verbose_name_plural = 'Media items'

    def save(self, *args, **kwargs):
        """Privacy depends on the tweet (which depends on its user), so ensure
        it's set correctly.
        """
        self.is_private = self.tweet.is_private
        super().save(*args, **kwargs)

    @property
    def large_url(self):
        return '%s:large' % self.image_url

    @property
    def medium_url(self):
        return '%s:medium' % self.image_url

    @property
    def small_url(self):
        return '%s:small' % self.image_url

    @property
    def thumb_url(self):
        return '%s:thumb' % self.image_url


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

    ditto_item_name = 'twitter_tweet'

    user = models.ForeignKey('User')

    text = models.TextField(null=False, blank=False, max_length=140)
    text_html = models.TextField(null=False, blank=True,
        help_text="An HTMLified version of the Tweet's text")
    twitter_id = models.BigIntegerField(null=False, blank=False, unique=True,
                                                                db_index=True)

    # Favorite and Retweet Count not present in tweets ingested from a
    # downloaded archive, hence null=True:
    favorite_count = models.PositiveIntegerField(null=True, blank=True,
        help_text="Approximately how many times this had been favorited when fetched")
    retweet_count = models.PositiveIntegerField(null=True, blank=True,
        help_text="Number of times this had been retweeted when fetched")

    in_reply_to_screen_name = models.CharField(null=False, blank=True,
        max_length=20,
        help_text="Screen name of the original Tweet's author, if this is a reply")
    in_reply_to_status_id = models.BigIntegerField(null=True, blank=True,
        help_text="The ID of the Tweet replied to, if any")
    in_reply_to_user_id = models.BigIntegerField(null=True, blank=True,
        help_text="ID of the original Tweet's author, if this is a reply")

    language = models.CharField(null=False, blank=False, default='und',
        max_length=20,
        help_text="A BCP 47 language identifier, or 'und' if it couldn't be detected")

    # Just enough of the place data to display something readable and useful:
    place_attribute_street_address = models.CharField(null=False, blank=True,
                                                                max_length=255)
    place_full_name = models.CharField(null=False, blank=True, max_length=255)
    place_country = models.CharField(null=False, blank=True, max_length=255)

    quoted_status_id = models.BigIntegerField(null=True, blank=True,
        help_text="The ID of the Tweet quoted, if any")

    source = models.CharField(null=False, blank=True, max_length=255,
                                help_text="Utility used to post the Tweet")
    media_count = models.PositiveSmallIntegerField(null=False, blank=True,
        default=0, help_text="Number of Photos/Videos attached to this Tweet")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-post_time']

    def save(self, *args, **kwargs):
        "Privacy depends on the user, so ensure it's set correctly"
        self.is_private = self.user.is_private
        result = self.make_text_html()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        if self.user:
            return reverse('twitter:tweet_detail', kwargs={
                                        'screen_name': self.user.screen_name,
                                        'twitter_id': self.twitter_id})
        else:
            return ''

    def get_next_public_by_post_time(self):
        "Next Tweet by this User, if they're public."
        try:
            return Tweet.public_tweet_objects.filter(post_time__gte=self.post_time, user=self.user).exclude(pk=self.pk).order_by('post_time')[:1].get()
        except:
            pass

    def get_previous_public_by_post_time(self):
        "Previous Tweet by this User, if they're public."
        try:
            return Tweet.public_tweet_objects.filter(post_time__lte=self.post_time, user=self.user).exclude(pk=self.pk).order_by('-post_time')[:1].get()
        except:
            pass

    # Shortcuts:
    def get_next(self):
        return self.get_next_public_by_post_time()

    def get_previous(self):
        return self.get_previous_public_by_post_time()

    @property
    def is_reply(self):
        if self.in_reply_to_screen_name == '':
            return False
        else:
            return True

    @property
    def in_reply_to_url(self):
        "If it's a reply, the link to the tweet replied to."
        if self.is_reply:
            return 'https://twitter.com/%s/status/%s' % (
                    self.in_reply_to_screen_name, self.in_reply_to_status_id)
        else:
            return ''

    @property
    def place(self):
        return ', '.join(filter(None, (
                self.place_attribute_street_address,
                self.place_full_name,
                self.place_country,
            )))

    @property
    def account(self):
        "The Account whose tweet this is, if any. Otherwise, None."
        try:
            return self.user.account_set.all()[0]
        except IndexError:
            return None

    def summary_source(self):
        "The text that will be truncated to make a summary for this Tweet"
        return self.text

    def make_text_html(self):
        """Uses the raw JSON for the tweet to set self.text_html to a nice
        HTML version of the tweet.
        """
        try:
            json_data = json.loads(self.raw)
        except ValueError as error:
            return False
        self.text_html = htmlify_tweet(json_data)
        return True

    def get_quoted_tweet(self):
        # There's one we saved earlier, so use that.
        if hasattr(self, '_quoted_tweet'):
            return self._quoted_tweet

        tweet = None
        if self.quoted_status_id:
            try:
                tweet = Tweet.public_objects.get(
                                            twitter_id=self.quoted_status_id)
            except Tweet.DoesNotExist:
                pass

        # Save for later:
        self._quoted_tweet = tweet
        return tweet


class User(TimeStampedModelMixin, DiffModelMixin, models.Model):
    """A Twitter user.
    We don't replicate all of the possible User attributes here, only enough
    to display the most useful things.
    """

    twitter_id = models.BigIntegerField(null=False, blank=False, unique=True)
    screen_name = models.CharField(null=False, blank=False, max_length=20,
        help_text="Username, eg, 'samuelpepys'")
    name = models.CharField(null=False, blank=False, max_length=30,
        help_text="eg, 'Samuel Pepys'")
    url = models.URLField(null=False, blank=True, default='',
        help_text="A URL provided by the user as part of their profile")
    # Inverse of Twitter's 'protected', to be similar to DittoItemModel:
    is_private = models.BooleanField(null=False, default=False,
        help_text="True if this user is 'protected'")
    is_verified = models.BooleanField(null=False, default=False)

    # User data in ingested archives don't have this:
    created_at = models.DateTimeField(null=True, blank=True,
        help_text="UTC time when this account was created on Twitter")

    description = models.CharField(null=False, blank=True, max_length=255)
    description_html = models.TextField(null=False, blank=True,
                help_text="An HTMLified version of the User's description")
    location = models.CharField(null=False, blank=True, max_length=255)
    time_zone = models.CharField(null=False, blank=True, max_length=255)

    profile_image_url_https = models.URLField(null=False, blank=True,
                                                                max_length=255)

    # This is how it's spelt in the API:
    favourites_count = models.PositiveIntegerField(null=False, blank=False,
        default=0,
        help_text="The number of tweets this user has favorited in the account’s lifetime")
    followers_count = models.PositiveIntegerField(null=False, blank=False,
        default=0,
        help_text="The number of followers this account has")
    friends_count = models.PositiveIntegerField(null=False, blank=False,
        default=0,
        help_text="Tne number of users this account is following.")
    listed_count = models.PositiveIntegerField(null=False, blank=False,
        default=0,
        help_text="The number of public lists this user is a member of")
    statuses_count = models.PositiveIntegerField(null=False, blank=False,
        default=0,
        help_text="The number of tweets, including retweets, by this user")

    # As on DittoItemModel:
    fetch_time = models.DateTimeField(null=True, blank=True,
                            help_text="The time the data was last fetched.")
    raw = models.TextField(null=False, blank=True,
                                    help_text="eg, the raw JSON from the API.")

    def avatar_upload_path(self, filename):
        "Make path under MEDIA_ROOT where avatar file will be saved."
        dirbase = getattr(settings, 'DITTO_TWITTER_DIR_BASE', 'twitter')
        return '/'.join([
            dirbase,
            str(self.twitter_id),
            'avatars',
            str(filename)
        ])

    avatar = models.ImageField(upload_to=avatar_upload_path,
                                            null=False, blank=True, default='')

    favorites = models.ManyToManyField(Tweet, related_name="favoriting_users")

    objects = models.Manager()
    # All Users that have Accounts:
    objects_with_accounts = managers.WithAccountsManager()

    def __str__(self):
        return '@%s' % self.screen_name

    class Meta:
        ordering = ['screen_name']

    def save(self, *args, **kwargs):
        """If the user's privacy status has changed, we need to change the
        privacy of all their tweets
        And we also HTMLify their description.
        """
        if self.get_field_diff('is_private') is not None:
            Tweet.objects.filter(user=self).update(is_private=self.is_private)
        result = self.make_description_html()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('twitter:user_detail',
                    kwargs={'screen_name': self.screen_name})

    def make_description_html(self):
        """Uses the raw JSON for the user to set self.description_html to a nice
        HTML version of the description.
        """
        try:
            json_data = json.loads(self.raw)
        except ValueError as error:
            return False
        self.description_html = htmlify_description(json_data)
        return True

    @property
    def permalink(self):
        return 'https://twitter.com/%s' % self.screen_name

    @property
    def avatar_url(self):
        try:
            return self.avatar.url
        except ValueError:
            return static('img/default_avatar.png')

    @property
    def profile_image_url(self):
        return self.profile_image_url_https

    @property
    def favorites_count(self):
        return self.favourites_count

