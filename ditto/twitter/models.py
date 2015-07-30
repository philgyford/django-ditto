# coding: utf-8
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from ditto.ditto.models import DiffModelMixin, DittoItemModel, TimeStampedModelMixin


@python_2_unicode_compatible
class Account(TimeStampedModelMixin, models.Model):
    """The Twitter User Accounts with which we fetch data from the API.
    Each one is connected to a User object, so we only need to store API
    details here.
    """

    user = models.ForeignKey('User', blank=True, null=True,
                                                    on_delete=models.SET_NULL)

    consumer_key = models.CharField(null=False, blank=True, max_length=255,
            help_text="(API Key)")
    consumer_secret = models.CharField(null=False, blank=True, max_length=255,
            help_text="(API Secret)")
    access_token = models.CharField(null=False, blank=True, max_length=255)
    access_token_secret = models.CharField(null=False, blank=True,
                                                                max_length=255)

    def __str__(self):
        if self.user:
            return self.user.screen_name
        else:
            return '%d' % self.pk

    class Meta:
        ordering = ['-time_created']

    #def get_absolute_url(self):
        #from django.core.urlresolvers import reverse
        #return reverse('twitter:account_detail', kwargs={''})


class Tweet(DittoItemModel):
    """We don't replicate all of the possible Tweet attributes here, only
    enough to display the most useful things. Given we save the raw JSON
    about this tweet, we could add more attributes in future, even if original
    tweets are deleted on Twitter.

    Also, we don't include any 'perspectival' attributes - ones that will vary
    depending on which Account fetched this data. eg, `favorited` or
    `current_user_retweet`.
    """
    user = models.ForeignKey('User')

    text = models.CharField(null=False, blank=False, max_length=255)
    twitter_id = models.BigIntegerField(null=False, blank=False, unique=True)
    twitter_id_str = models.CharField(null=False, blank=False, unique=True,
                                                                max_length=20)
    created_at = models.DateTimeField(null=False, blank=False,
            help_text="UTC time when this Tweet was created on Twitter")
    favorite_count = models.PositiveIntegerField(null=False, blank=False,
            default=0,
            help_text="Approximately how many times this has been favorited")
    retweet_count = models.PositiveIntegerField(null=False, blank=False,
            default=0,
            help_text="Number of times this has been retweeted")

    in_reply_to_screen_name = models.CharField(null=False, blank=True,
        max_length=20,
        help_text="Screen name of the original Tweet's author, if this is a reply")
    in_reply_to_status_id = models.BigIntegerField(null=True, blank=True,
            help_text="The ID of the Tweet replied to, if any")
    in_reply_to_status_id_str = models.CharField(null=False, blank=True,
                                                                max_length=20)
    in_reply_to_user_id = models.BigIntegerField(null=True, blank=True,
            help_text="ID of the original Tweet's author, if this is a reply")
    in_reply_to_user_id_str = models.CharField(null=False, blank=True,
                                                                max_length=20)

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
    quoted_status_id_str = models.CharField(null=False, blank=True,
                                                                max_length=20)

    source = models.CharField(null=False, blank=True, max_length=255,
                                help_text="Utility used to post the Tweet")

    def __str__(self):
        return self.text

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        "Privacy depends on the user, so ensure it's set correctly"
        self.is_private = self.user.is_private
        super(Tweet, self).save(*args, **kwargs)

    #def get_absolute_url(self):
        #from django.core.urlresolvers import reverse
        #return reverse('pinboard:bookmark_detail',
                    #kwargs={'username': self.account.username, 'pk': self.id})

    def summary_source(self):
        "The text that will be truncated to make a summary for this Tweet"
        return self.text


class User(TimeStampedModelMixin, DiffModelMixin, models.Model):
    """A Twitter user.
    We don't replicate all of the possible User attributes here, only enough
    to display the most useful things.
    """

    twitter_id = models.BigIntegerField(null=False, blank=False, unique=True)
    twitter_id_str = models.CharField(null=False, blank=False, unique=True,
                                                                max_length=20)
    screen_name = models.CharField(null=False, blank=False, max_length=20,
        help_text="Username, eg, 'samuelpepys'")
    name = models.CharField(null=False, blank=False, max_length=30,
        help_text="eg, 'Samuel Pepys'")
    url = models.URLField(null=False, blank=True,
        help_text="A URL provided by the user as part of their profile")
    # Inverse of Twitter's 'protected', to be similar to DittoItemModel:
    is_private = models.BooleanField(null=False, default=False,
        help_text="True if this user is 'protected' or private")
    is_verified = models.BooleanField(null=False, default=False)

    created_at = models.DateTimeField(null=False, blank=False,
        help_text="UTC time when this account was created on Twitter")

    description = models.CharField(null=False, blank=True, max_length=255)
    location = models.CharField(null=False, blank=True, max_length=255)
    time_zone = models.CharField(null=False, blank=True, max_length=255)

    profile_image_url = models.URLField(null=False, blank=True, max_length=255)
    profile_image_url_https = models.URLField(null=False, blank=True,
                                                                max_length=255)

    favorites_count = models.PositiveIntegerField(null=False, blank=False,
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
        help_text="The time the data was last fetched, and was new or changed.")
    raw = models.TextField(null=False, blank=True,
                                    help_text="eg, the raw JSON from the API.")

    def __str__(self):
        return self.screen_name

    class Meta:
        ordering = ['screen_name']

    def save(self, *args, **kwargs):
        """If the user's privacy status has changed, we need to change the
        privacy of all their tweets
        """
        if self.get_field_diff('is_private') is not None:
            Tweet.objects.filter(user=self).update(is_private=self.is_private)
        super(User, self).save(*args, **kwargs)

    @property
    def permalink(self):
        return 'https://twitter.com/%s' % self.screen_name

    #def get_absolute_url(self):
        #from django.core.urlresolvers import reverse
        #return reverse('twitter:account_detail', kwargs={''})

