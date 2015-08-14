from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput

from .models import Account, Tweet, User


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'time_created', 'time_modified',)

    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('API', {
            'fields': ('consumer_key', 'consumer_secret', 'access_token', 'access_token_secret',),
            'description': 'Keys and secrets require creation of an app at <a href="https://apps.twitter.com/">apps.twitter.com</a>',
        }),
        ('Data', {
            'fields': ('last_fetch_id', 'time_created', 'time_modified',)
        }),
    )
    readonly_fields = ('time_created', 'time_modified',)

@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'title', )
    list_display_links = ('title', )
    list_filter = ('user', 'created_at',)

    fieldsets = (
        (None, {
            'fields': ('user', 'text', 'title', 'summary', 'created_at', 'is_private',
                'twitter_id', 'permalink', )
        }),
        (None, {
            'fields': ('favorite_count', 'retweet_count', 'language',
                'source', 'in_reply_to_screen_name', 'in_reply_to_status_id',
                'in_reply_to_user_id', 'quoted_status_id', )
        }),
        ('Location', {
            'fields': ('latitude', 'longitude',
                'place_attribute_street_address', 'place_full_name',
                'place_country')
        }),
        ('Data', {
            'fields': ('raw', 'fetch_time', 'time_created', 'time_modified',)
        }),
    )

    formfield_overrides = {
        # Make the inputs full-width.
        models.CharField: {'widget': TextInput(
            attrs={
                'class': 'vLargeTextField',
            }
        )},
        # Reduce the number of rows.
        models.TextField: {'widget': Textarea(
            attrs={
                'class': 'vLargeTextField',
                'cols': 40,
                'rows': 5,
            }
        )},
    }
    readonly_fields = ('time_created', 'time_modified',)
    search_fields = ('text', )

admin.site.register(User)

