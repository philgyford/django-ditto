from django.contrib import admin

from ..core.admin import DittoItemModelAdmin
from .models import Account, Album, Artist, Scrobble, Track


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "realname",
        "is_active",
        "time_created",
    )
    search_fields = (
        "name",
        "artist",
        "mbid",
    )

    fieldsets = (
        (None, {"fields": ("username", "realname", "api_key", "is_active",)}),
        ("Data", {"fields": ("time_created", "time_modified",)}),
    )

    readonly_fields = (
        "time_created",
        "time_modified",
    )


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "mbid",
        "time_created",
    )
    search_fields = (
        "name",
        "mbid",
    )

    fieldsets = (
        (None, {"fields": ("name", "slug", "original_slug", "mbid",)}),
        ("Data", {"fields": ("time_created", "time_modified",)}),
    )

    readonly_fields = (
        "time_created",
        "time_modified",
    )


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "artist",
        "mbid",
        "time_created",
    )
    search_fields = (
        "name",
        "artist__name",
        "mbid",
    )

    fieldsets = (
        (None, {"fields": ("name", "slug", "original_slug", "artist", "mbid",)}),
        ("Data", {"fields": ("time_created", "time_modified",)}),
    )

    readonly_fields = (
        "time_created",
        "time_modified",
    )
    raw_id_fields = ("artist",)


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "artist",
        "mbid",
        "time_created",
    )
    search_fields = (
        "name",
        "artist__name",
    )

    fieldsets = (
        (None, {"fields": ("name", "slug", "original_slug", "artist", "mbid",)}),
        ("Data", {"fields": ("time_created", "time_modified",)}),
    )

    readonly_fields = (
        "time_created",
        "time_modified",
    )
    raw_id_fields = ("artist",)


@admin.register(Scrobble)
class ScrobbleAdmin(DittoItemModelAdmin):
    list_display = (
        "title",
        "post_time",
    )
    list_filter = ("post_time",)
    search_fields = (
        "title",
        "track__name",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "account",
                    "artist",
                    "track",
                    "album",
                    "post_time",
                    "post_year_str",
                )
            },
        ),
        ("Data", {"fields": ("raw", "fetch_time", "time_created", "time_modified",)}),
    )

    raw_id_fields = (
        "artist",
        "track",
        "album",
    )
    readonly_fields = (
        "post_year_str",
        "raw",
        "fetch_time",
        "time_created",
        "time_modified",
    )
