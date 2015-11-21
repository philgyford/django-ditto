# coding: utf-8
from django.db import models

from . import managers
from ..ditto.models import DiffModelMixin, DittoItemModel, TimeStampedModelMixin


class Account(TimeStampedModelMixin, models.Model):
    user = models.ForeignKey('User', blank=True, null=True,
                                                    on_delete=models.SET_NULL)

    api_key = models.CharField(null=False, blank=True, max_length=255,
                                                        verbose_name='API Key')
    api_secret = models.CharField(null=False, blank=True, max_length=255,
                                                    verbose_name='API Secret')

    is_active = models.BooleanField(default=True, null=False, blank=False,
                        help_text="If false, new Photos won't be fetched.")

    def __str__(self):
        if self.user:
            return str(self.user)
        else:
            return '%d' % self.pk

    class Meta:
        ordering = ['user__username']

    def hasCredentials(self):
        "Does this at least have something in its API fields? True or False"
        if self.api_key and self.api_secret:
            return True
        else:
            return False


class User(TimeStampedModelMixin, DiffModelMixin, models.Model):
    nsid = models.CharField(null=False, blank=False, unique=True,
                                        max_length=50, verbose_name='NSID')
    is_pro = models.BooleanField(null=False, blank=False, default=False,
                                                    verbose_name='Is Pro?')
    iconserver = models.CharField(null=False, blank=False, max_length=20)
    iconfarm = models.PositiveIntegerField(null=False, blank=False)

    username = models.CharField(null=False, blank=False, unique=True,
                                                                  max_length=50)
    realname = models.CharField(null=False, blank=False, max_length=255)
    location = models.CharField(null=False, blank=True, max_length=255)
    description = models.TextField(null=False, blank=True,
                                                help_text="May contain HTML")

    photos_url = models.URLField(null=False, blank=False, max_length=255,
                                                    verbose_name='Photos URL')
    profile_url = models.URLField(null=False, blank=False, max_length=255,
                                                    verbose_name='Profile URL')

    photos_count = models.PositiveIntegerField(null=False, blank=False,
                                                                      default=0)
    photos_views = models.PositiveIntegerField(null=False, blank=False,
                                                                      default=0)
    photos_first_date = models.DateTimeField(null=True, blank=False)
    photos_first_date_taken = models.DateTimeField(null=True, blank=False)

    # As on DittoItemModel:
    fetch_time = models.DateTimeField(null=True, blank=True,
        help_text="The time the data was last fetched, and was new or changed.")
    raw = models.TextField(null=False, blank=True,
                                    help_text="eg, the raw JSON from the API.")

    objects = models.Manager()
    # All Users that have Accounts:
    objects_with_accounts = managers.WithAccountsManager()

    def __str__(self):
        return self.realname

    class Meta:
        ordering = ['realname']

    @property
    def name(self):
        return self.realname

