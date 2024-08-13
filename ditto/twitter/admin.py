from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput
from django.utils.safestring import mark_safe

from ditto.core.admin import DittoItemModelAdmin

from .models import Account, Media, Tweet, User


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "is_active",
        "time_created",
        "time_modified",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "is_active",
                )
            },
        ),
        (
            "API",
            {
                "fields": (
                    "consumer_key",
                    "consumer_secret",
                    "access_token",
                    "access_token_secret",
                ),
                "description": (
                    "Keys and secrets require creation of an app at "
                    '<a href="https://developer.twitter.com/portal">'
                    "developer.twitter.com/portal</a>"
                ),
            },
        ),
        (
            "Data",
            {
                "fields": (
                    "last_recent_id",
                    "last_favorite_id",
                    "time_created",
                    "time_modified",
                )
            },
        ),
    )

    formfield_overrides = {
        # Make the inputs full-width.
        models.CharField: {"widget": TextInput(attrs={"class": "vLargeTextField"})},
    }

    readonly_fields = (
        "time_created",
        "time_modified",
    )


class TweetsMediaInline(admin.TabularInline):
    model = Media.tweets.through
    extra = 0
    raw_id_fields = (
        "media",
        "tweet",
    )


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = (
        "show_thumb",
        "media_type",
        "time_created",
    )
    list_display_links = ("show_thumb",)
    list_filter = ("time_created",)
    date_hierarchy = "time_created"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "show_image",
                    "media_type",
                    "twitter_id",
                    "image_url",
                    "image_file",
                    "mp4_file",
                ),
            },
        ),
        (
            "Sizes",
            {
                "classes": ("collapse",),
                "fields": (
                    "large_w",
                    "large_h",
                    "medium_w",
                    "medium_h",
                    "small_w",
                    "small_h",
                    "thumb_w",
                    "thumb_h",
                ),
            },
        ),
        (
            "Video",
            {
                "classes": ("collapse",),
                "fields": (
                    "aspect_ratio",
                    "duration",
                    "mp4_url",
                    "dash_url",
                    "xmpeg_url",
                ),
            },
        ),
        (
            "Data",
            {
                "classes": ("collapse",),
                "fields": (
                    "time_created",
                    "time_modified",
                ),
            },
        ),
    )

    inlines = [
        TweetsMediaInline,
    ]

    readonly_fields = (
        "show_image",
        "time_created",
        "time_modified",
    )
    exclude = ("tweets",)

    def show_thumb(self, instance):
        return mark_safe(
            f'<img src="{instance.thumbnail_url}" width="{instance.thumbnail_w}" '
            f'height="{instance.thumbnail_h}" />'
        )

    show_thumb.short_description = ""

    def show_image(self, instance):
        if instance.media_type == "photo":
            html = (
                f'<img src="{instance.small_url}" width="{instance.small_w}" '
                f'height="{instance.small_h}" />'
            )
        else:
            html = (
                f'<video width="{instance.small_w}" height="{instance.small_h}" '
                f'poster="{instance.small_url}" controls preload="metadata">'
                f'<source src="{instance.video_url}" type="{instance.video_mime_type}">'
                "</video>"
            )
        return mark_safe(html)

    show_image.short_description = "Image"


@admin.register(Tweet)
class TweetAdmin(DittoItemModelAdmin):
    list_display = (
        "user",
        "is_private",
        "title",
        "post_time",
    )
    list_display_links = ("title",)
    list_filter = (
        "post_time",
        "fetch_time",
    )
    search_fields = ("text",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "text",
                    "text_html",
                    "title",
                    "summary",
                    "post_time",
                    "post_year_str",
                    "is_private",
                    "twitter_id",
                    "permalink",
                )
            },
        ),
        (
            None,
            {
                "fields": (
                    "favorite_count",
                    "retweet_count",
                    "media_count",
                    "language",
                    "source",
                    "in_reply_to_screen_name",
                    "in_reply_to_status_id",
                    "in_reply_to_user_id",
                    "quoted_status_id",
                    "retweeted_status_id",
                )
            },
        ),
        (
            "Location",
            {
                "classes": ("collapse",),
                "fields": (
                    "latitude",
                    "longitude",
                    "place_attribute_street_address",
                    "place_full_name",
                    "place_country",
                ),
            },
        ),
        (
            "Data",
            {
                "classes": ("collapse",),
                "fields": (
                    "raw",
                    "fetch_time",
                    "time_created",
                    "time_modified",
                ),
            },
        ),
    )

    readonly_fields = (
        "post_year_str",
        "text_html",
        "raw",
        "fetch_time",
        "time_created",
        "time_modified",
    )

    inlines = [
        TweetsMediaInline,
    ]

    formfield_overrides = {
        # Make the inputs full-width.
        models.CharField: {"widget": TextInput(attrs={"class": "vLargeTextField"})},
        # Reduce the number of rows.
        models.TextField: {
            "widget": Textarea(
                attrs={"class": "vLargeTextField", "cols": 40, "rows": 5}
            )
        },
    }


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "show_avatar",
        "screen_name",
        "name",
        "is_private",
        "fetch_time",
    )
    list_display_links = (
        "show_avatar",
        "screen_name",
    )
    search_fields = (
        "screen_name",
        "name",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "screen_name",
                    "name",
                    "is_private",
                    "is_verified",
                    "profile_image_url_https",
                    "avatar",
                    "url",
                    "description",
                    "description_html",
                    "location",
                    "time_zone",
                    "twitter_id",
                    "created_at",
                )
            },
        ),
        (
            "Data",
            {
                "fields": (
                    "raw",
                    "fetch_time",
                    "time_created",
                    "time_modified",
                )
            },
        ),
    )

    formfield_overrides = {
        # Make the inputs full-width.
        models.CharField: {"widget": TextInput(attrs={"class": "vLargeTextField"})},
    }

    readonly_fields = (
        "description_html",
        "raw",
        "fetch_time",
        "time_created",
        "time_modified",
    )

    def show_avatar(self, instance):
        return mark_safe(f'<img src="{instance.avatar_url}" width="24" height="24" />')

    show_avatar.short_description = ""
