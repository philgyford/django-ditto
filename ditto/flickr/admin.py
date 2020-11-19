from django.contrib import admin
from django.db import models
from django.forms import TextInput
from django.utils.safestring import mark_safe

from ..core.admin import DittoItemModelAdmin
from .models import Account, Photo, Photoset, User


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "has_credentials",
        "is_active",
        "time_created",
        "time_modified",
    )

    fieldsets = (
        (None, {"fields": ("user", "is_active",)}),
        (
            "API",
            {
                "fields": ("api_key", "api_secret",),
                "description": (
                    "Keys and secrets require creation of an app at "
                    '<a href="https://www.flickr.com/services/apps/create/apply/">'
                    "flickr.com/...</a>"
                ),
            },
        ),
        (
            "Data",
            {"classes": ("collapse",), "fields": ("time_created", "time_modified",)},
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

    def has_credentials(self, obj):
        return obj.has_credentials()

    has_credentials.boolean = True


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "show_avatar",
        "realname",
        "username",
        "fetch_time",
    )
    list_display_links = (
        "show_avatar",
        "realname",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "realname",
                    "username",
                    "nsid",
                    "is_pro",
                    "location",
                    "description",
                    "photos_url",
                    "profile_url",
                    "avatar",
                    "photos_count",
                    "photos_views",
                    "photos_first_date",
                    "photos_first_date_taken",
                    "timezone_id",
                )
            },
        ),
        (
            "Data",
            {
                "classes": ("collapse",),
                "fields": (
                    "iconserver",
                    "iconfarm",
                    "raw",
                    "fetch_time",
                    "time_created",
                    "time_modified",
                ),
            },
        ),
    )
    readonly_fields = (
        "raw",
        "fetch_time",
        "time_created",
        "time_modified",
    )
    search_fields = (
        "realname",
        "username",
    )

    def show_avatar(self, instance):
        return mark_safe(
            '<img src="%s" width="24" height="24" />' % (instance.avatar_url)
        )

    show_avatar.short_description = ""


@admin.register(Photoset)
class PhotosetAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "flickr_created_time",
        "fetch_time",
    )
    list_display_links = ("title",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "title",
                    "description",
                    "primary_photo",
                    "flickr_id",
                    "photo_count",
                    "video_count",
                    "view_count",
                    "comment_count",
                    "last_update_time",
                    "flickr_created_time",
                    "photos",
                )
            },
        ),
        (
            "Data",
            {
                "classes": ("collapse",),
                "fields": ("raw", "fetch_time", "time_created", "time_modified",),
            },
        ),
    )
    readonly_fields = (
        "raw",
        "fetch_time",
        "time_created",
        "time_modified",
    )
    search_fields = (
        "title",
        "description",
    )
    raw_id_fields = (
        "primary_photo",
        "photos",
    )


class TaggedPhotoInline(admin.TabularInline):
    model = Photo.tags.through
    raw_id_fields = ("tag",)


@admin.register(Photo)
class PhotoAdmin(DittoItemModelAdmin):
    list_display = (
        "title",
        "show_thumb",
        "post_time",
        "taken_time",
    )
    list_display_links = (
        "title",
        "show_thumb",
    )
    list_filter = (
        "post_time",
        "fetch_time",
    )
    date_hierarchy = "post_time"
    search_fields = [
        "title",
        "description",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "show_image",
                    "user",
                    "title",
                    "description",
                    "summary",
                    "permalink",
                    "is_private",
                    "flickr_id",
                    "media",
                    "license",
                    "original_file",
                    "video_original_file",
                )
            },
        ),
        (
            "Times",
            {
                "classes": ("collapse",),
                "fields": (
                    "post_time",
                    "post_year_str",
                    "last_update_time",
                    "taken_time",
                    "taken_year_str",
                    "taken_granularity",
                    "taken_unknown",
                ),
            },
        ),
        (
            "Counts, secrets, server, etc",
            {
                "classes": ("collapse",),
                "fields": (
                    "view_count",
                    "comment_count",
                    "secret",
                    "original_secret",
                    "server",
                    "farm",
                    "rotation",
                    "original_format",
                    "safety_level",
                    "has_people",
                ),
            },
        ),
        (
            "Sizes",
            {
                "classes": ("collapse",),
                "fields": (
                    ("thumbnail_width", "thumbnail_height",),
                    ("small_width", "small_height",),
                    ("small_320_width", "small_320_height",),
                    ("medium_width", "medium_height",),
                    ("medium_640_width", "medium_640_height",),
                    ("medium_800_width", "medium_800_height",),
                    ("large_width", "large_height",),
                    ("large_1600_width", "large_1600_height",),
                    ("large_2048_width", "large_2048_height",),
                    ("x_large_3k_width", "x_large_3k_height",),
                    ("x_large_4k_width", "x_large_4k_height",),
                    ("x_large_5k_width", "x_large_5k_height",),
                    ("x_large_6k_width", "x_large_6k_height",),
                    ("original_width", "original_height",),
                    ("mobile_mp4_width", "mobile_mp4_height",),
                    ("site_mp4_width", "site_mp4_height",),
                    ("hd_mp4_width", "hd_mp4_height",),
                    ("video_original_width", "video_original_height",),
                ),
            },
        ),
        (
            "Location",
            {
                "classes": ("collapse",),
                "fields": (
                    "geo_is_private",
                    ("latitude", "longitude",),
                    "location_accuracy",
                    "location_context",
                    "location_place_id",
                    "location_woeid",
                    "locality_name",
                    "locality_place_id",
                    "locality_woeid",
                    "county_name",
                    "county_place_id",
                    "county_woeid",
                    "region_name",
                    "region_place_id",
                    "region_woeid",
                    "country_name",
                    "country_place_id",
                    "country_woeid",
                ),
            },
        ),
        (
            "EXIF",
            {
                "classes": ("collapse",),
                "fields": (
                    "exif_camera",
                    "exif_lens_model",
                    "exif_aperture",
                    "exif_exposure",
                    "exif_flash",
                    "exif_focal_length",
                    "exif_iso",
                ),
            },
        ),
        (
            "Data",
            {
                "classes": ("collapse",),
                "fields": (
                    "raw",
                    "sizes_raw",
                    "exif_raw",
                    "fetch_time",
                    "time_created",
                    "time_modified",
                ),
            },
        ),
    )
    radio_fields = {"media": admin.HORIZONTAL}
    readonly_fields = (
        "post_year_str",
        "taken_year_str",
        "show_image",
        "raw",
        "fetch_time",
        "time_created",
        "time_modified",
        "sizes_raw",
        "exif_raw",
    )

    formfield_overrides = {
        # Make the inputs full-width.
        models.CharField: {"widget": TextInput(attrs={"class": "vLargeTextField"})},
    }
    inlines = [
        TaggedPhotoInline,
    ]
    raw_id_fields = ("user",)

    def show_thumb(self, instance):
        return mark_safe(
            '<img src="%s" width="%s" height="%s" />'
            % (
                instance.thumbnail_url,
                instance.thumbnail_width,
                instance.thumbnail_height,
            )
        )

    show_thumb.short_description = "Thumbnail"

    def show_image(self, instance):
        return mark_safe(
            '<img src="%s" width="%s" height="%s" />'
            % (instance.small_url, instance.small_width, instance.small_height)
        )

    show_image.short_description = "Small image"

    def taken_year_str(self, instance):
        "So Admin doesn't add a comma, like '2,016'."
        return str(instance.taken_year)

    taken_year_str.short_description = "Taken year"
