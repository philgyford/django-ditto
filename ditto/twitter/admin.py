from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput

from .models import Account, Tweet, User


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_credentials', 'time_created', 'time_modified',)

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

    formfield_overrides = {
        # Make the inputs full-width.
        models.CharField: {'widget': TextInput(
            attrs={
                'class': 'vLargeTextField',
            }
        )},
    }

    readonly_fields = ('time_created', 'time_modified',)

    def has_credentials(self, obj):
        return obj.hasCredentials()
    has_credentials.boolean = True


@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ('user','is_private', 'title', 'created_at', )
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


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('screen_name', 'name', 'is_private', 'fetch_time')
    list_display_links = ('screen_name', )

    fieldsets = (
        (None, {
            'fields': ('screen_name', 'name',
                'is_private', 'is_verified',
                'profile_image_url', 'profile_image_url_https',
                'url', 'description', 'location', 'time_zone',
                'twitter_id', 'created_at',
            )
        }),
        ('Data', {
            'fields': ('raw', 'fetch_time', 'time_created', 'time_modified',)
        }),
    )
    readonly_fields = ('time_created', 'time_modified',)
    search_fields = ('screen_name', 'name')

