# coding: utf-8
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from ditto.ditto.models import DittoItemModel, TimeStampedModelMixin


@python_2_unicode_compatible
class Account(TimeStampedModelMixin, models.Model):
    """The Twitter User Accounts with which we fetch data from the API.
    Each one is connected to a User object, so we only need to store API
    details here.
    """

    screen_name = models.CharField(null=False, blank=True, max_length=20,
            help_text="eg 'philgyford'")
    consumer_key = models.CharField(null=False, blank=True, max_length=255,
            help_text="(API Key)")
    consumer_secret = models.CharField(null=False, blank=True, max_length=255,
            help_text="(API Secret)")
    access_token = models.CharField(null=False, blank=True, max_length=255)
    access_token_secret = models.CharField(null=False, blank=True, max_length=255)

    def __str__(self):
        return self.screen_name

    class Meta:
        ordering = ['screen_name']

    #def get_absolute_url(self):
        #from django.core.urlresolvers import reverse
        #return reverse('twitter:account_detail', kwargs={''})

