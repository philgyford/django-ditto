from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput

from taggit.managers import TaggableManager
from taggit.forms import TagWidget

from ..core.admin import DittoItemModelAdmin
from .models import Account, Bookmark


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "is_active",
        "time_created",
        "time_modified",
    )

    fieldsets = (
        (None, {"fields": ("username", "url", "is_active",)}),
        (
            "API",
            {
                "fields": ("api_token",),
                "description": (
                    "Your API Token can be found at "
                    '<a href="https://pinboard.in/settings/password">'
                    "pinboard.in/settings/password</a>"
                ),
            },
        ),
        ("Data", {"fields": ("time_created", "time_modified",)}),
    )
    readonly_fields = (
        "time_created",
        "time_modified",
    )


@admin.register(Bookmark)
class BookmarkAdmin(DittoItemModelAdmin):
    list_display = (
        "title",
        "post_time",
        "account",
    )
    list_filter = (
        "post_time",
        "is_private",
        "to_read",
        "account",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "account",
                    "title",
                    "url",
                    "description",
                    "summary",
                    "tags",
                    "post_time",
                    "post_year_str",
                    "url_hash",
                )
            },
        ),
        ("Options", {"fields": ("is_private", "to_read",)}),
        ("Data", {"fields": ("raw", "fetch_time", "time_created", "time_modified",)}),
    )

    formfield_overrides = {
        # Make the inputs full-width.
        models.CharField: {"widget": TextInput(attrs={"class": "vLargeTextField"})},
        # Reduce the number of rows; similar to Pinboard's description field.
        models.TextField: {
            "widget": Textarea(
                attrs={"class": "vLargeTextField", "cols": 40, "rows": 4}
            )
        },
        # Make the input full-width.
        TaggableManager: {"widget": TagWidget(attrs={"class": "vLargeTextField"})},
    }

    readonly_fields = (
        "post_year_str",
        "raw",
        "fetch_time",
        "time_created",
        "time_modified",
    )
    search_fields = (
        "title",
        "url",
        "description",
    )
