from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput

from .models import Account, Media, Tweet, User


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_credentials', 'is_active',
                    'time_created', 'time_modified',)

    fieldsets = (
        (None, {
            'fields': ('user', 'is_active', )
        }),
        ('API', {
            'fields': ('consumer_key', 'consumer_secret', 'access_token', 'access_token_secret',),
            'description': 'Keys and secrets require creation of an app at <a href="https://apps.twitter.com/">apps.twitter.com</a>',
        }),
        ('Data', {
            'fields': ('last_recent_id', 'last_favorite_id', 'time_created', 'time_modified',)
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


class MediaInline(admin.StackedInline):
    model = Media
    extra = 0

    fieldsets = (
        (None, {
            'fields': ('media_type', 'twitter_id', 'image_url', 'is_private', )
        }),
        ('Sizes', {
            'classes': ('collapse',),
            'fields': ('large_w', 'large_h', 'medium_w', 'medium_h', 'small_w', 'small_h', 'thumb_w', 'thumb_h', )
        }),
        ('Video', {
            'classes': ('collapse',),
            'fields': ('aspect_ratio', 'duration',
                        'mp4_url_1', 'mp4_bitrate_1',
                        'mp4_url_2', 'mp4_bitrate_2',
                        'mp4_url_3', 'mp4_bitrate_3',
                        'webm_url', 'webm_bitrate',
                        'dash_url',
                        'xmpeg_url',)
        }),
        ('Data', {
            'classes': ('collapse',),
            'fields': ('time_created', 'time_modified',)
        }),
    )

    readonly_fields = ('time_created', 'time_modified',)


@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ('user','is_private', 'title', 'post_time', )
    list_display_links = ('title', )
    list_filter = ('post_time', 'fetch_time', )

    inlines = [
        MediaInline,
    ]

    fieldsets = (
        (None, {
            'fields': ('user', 'text', 'text_html', 'title', 'summary', 'post_time', 'is_private',
                'twitter_id', 'permalink', )
        }),
        (None, {
            'fields': ('favorite_count', 'retweet_count', 'media_count',
                'language', 'source',
                'in_reply_to_screen_name', 'in_reply_to_status_id',
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
    readonly_fields = ('text_html', 'time_created', 'time_modified',)
    search_fields = ('text', )


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('screen_name', 'name', 'is_private', 'fetch_time')
    list_display_links = ('screen_name', )

    fieldsets = (
        (None, {
            'fields': ('screen_name', 'name',
                'is_private', 'is_verified',
                'profile_image_url_https',
                'url', 'description', 'location', 'time_zone',
                'twitter_id', 'created_at', )
        }),
        ('Data', {
            'fields': ('raw', 'fetch_time', 'time_created', 'time_modified',)
        }),
    )
    readonly_fields = ('time_created', 'time_modified',)
    search_fields = ('screen_name', 'name')

