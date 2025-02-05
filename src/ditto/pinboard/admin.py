from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput
from taggit.forms import TagWidget
from taggit.managers import TaggableManager

from ditto.core.admin import DittoItemModelAdmin

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
        (
            None,
            {
                "fields": (
                    "username",
                    "url",
                    "is_active",
                )
            },
        ),
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
        (
            "Data",
            {
                "fields": (
                    "time_created",
                    "time_modified",
                )
            },
        ),
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
                    "url",
                    "title",
                    "description",
                    "tags",
                    ("is_private", "to_read"),
                    "post_time",
                )
            },
        ),
        (
            "Raw data, times, etc.",
            {
                "classes": ("collapse",),
                "fields": (
                    "summary",
                    "url_hash",
                    "raw",
                    "post_year_str",
                    "fetch_time",
                    "time_created",
                    "time_modified",
                ),
            },
        ),
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
        "tags__name",
    )

    def get_changeform_initial_data(self, request):
        """
        If there's only one Account, set it as the initial value for
        the account field.
        (Unless it's already set from the GET values.)
        """
        initial_data = super().get_changeform_initial_data(request)
        if Account.objects.count() == 1 and "account" not in initial_data:
            initial_data["account"] = str(Account.objects.first().pk)
        return initial_data
