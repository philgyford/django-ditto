from django.contrib import admin
from django.db import models

from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('screen_name', 'time_created', 'time_modified',)

    fieldsets = (
        (None, {
            'fields': ('screen_name',)
        }),
        ('API', {
            'fields': ('consumer_key', 'consumer_secret', 'access_token', 'access_token_secret',),
            'description': 'Keys and secrets require creation of an app at <a href="https://apps.twitter.com/">apps.twitter.com</a>',
        }),
        ('Data', {
            'fields': ('time_created', 'time_modified',)
        }),
    )
    readonly_fields = ('time_created', 'time_modified',)

