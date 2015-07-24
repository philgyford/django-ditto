from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput

from .models import Account, Bookmark


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('username', 'url', 'api_token',)
        }),
        ('Data', {
            'fields': ('time_created', 'time_modified',)
        }),
    )
    readonly_fields = ('time_created', 'time_modified',)


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('title', 'post_time', 'account',)
    list_filter = ('post_time', 'is_private', 'to_read', 'account',)
    fieldsets = (
        (None, {
            'fields': ('account', 'title', 'url', 'description', 'summary', 'post_time',)
        }),
        ('Options', {
            'fields': ('is_private', 'to_read',)
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
        # Reduce the number of rows; similar to Pinboard's description field.
        models.TextField: {'widget': Textarea(
            attrs={
                'class': 'vLargeTextField',
                'cols': 40,
                'rows': 4,
            }
        )},
    }
    readonly_fields = ('raw', 'fetch_time', 'time_created', 'time_modified',)
    search_fields = ('title', 'url', 'description',)
