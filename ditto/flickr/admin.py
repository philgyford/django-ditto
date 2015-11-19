from django.contrib import admin
from django.db import models
from django.forms import TextInput

from .models import Account, User


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_credentials', 'is_active',
                    'time_created', 'time_modified',)

    fieldsets = (
        (None, {
            'fields': ('user', 'is_active', )
        }),
        ('API', {
            'fields': ('api_key', 'api_secret',),
            'description': 'Keys and secrets require creation of an app at <a href="https://www.flickr.com/services/apps/create/apply/">flickr.com/...</a>',
        }),
        ('Data', {
            'fields': ('time_created', 'time_modified',)
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


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('realname', 'username', 'fetch_time',)
    list_display_links = ('realname', )

    fieldsets = (
        (None, {
            'fields': ('realname', 'username', 'nsid',
                'is_pro', 'location', 'description',
                'photos_url', 'profile_url',
                'photos_count', 'photos_views',
                'photos_first_date', 'photos_first_date_taken', )
        }),
        ('Data', {
            'fields': ('iconserver', 'iconfarm', 'raw',
                        'fetch_time', 'time_created', 'time_modified',)
        }),
    )
    readonly_fields = ('raw', 'fetch_time', 'time_created', 'time_modified',)
    search_fields = ('realname', 'username',)

