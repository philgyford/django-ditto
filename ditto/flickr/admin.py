from django.contrib import admin
from django.db import models
from django.forms import TextInput

from .models import Account, Photo, User


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
        return obj.has_credentials()
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
                'photos_first_date', 'photos_first_date_taken', 'timezone_id',)
        }),
        ('Data', {
            'fields': ('iconserver', 'iconfarm', 'raw',
                        'fetch_time', 'time_created', 'time_modified',)
        }),
    )
    readonly_fields = ('raw', 'fetch_time', 'time_created', 'time_modified',)
    search_fields = ('realname', 'username',)


class TaggedPhotoInline(admin.TabularInline):
    model = Photo.tags.through
    raw_id_fields = ('tag',)

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'show_thumb', 'post_time', 'taken_time', )
    list_display_links = ('title', 'show_thumb',)
    list_filter = ('post_time', 'fetch_time', )
    date_hierarchy = 'post_time'
    search_fields = ['title', 'description',]

    fieldsets = (
        (None, {
            'fields': ('show_image', 'user', 'title', 'description', 'summary', 
                'permalink', 'is_private', 'flickr_id', 'media', 'license', )
        }),  
        ('Times', {
            'fields': ('post_time', 'last_update_time', 'taken_time', 'taken_granularity',
                'taken_unknown', )
        }),
        (None, {
            'fields': ('view_count', 'comment_count', 'secret', 'original_secret', 'server', 'farm',                 'rotation', 'original_format', 'safety_level', 'has_people')
        }),
        ('Sizes', {
            'fields': ('width_t', 'height_t', 'width_m', 'height_m', 'width_n', 'height_n', 'width', 'height', 'width_z', 'height_z', 'width_c', 'height_c', 'width_b', 'height_b', 'width_h', 'height_h', 'width_k', 'height_k', 'width_o', 'height_o', )
        }),
        ('Location', {
            'fields': ('geo_is_private', 'latitude', 'longitude', 'location_accuracy', 'location_context', 'location_place_id', 'location_woeid',
                'locality_name', 'locality_place_id', 'locality_woeid',
                'county_name', 'county_place_id', 'county_woeid',
                'region_name', 'region_place_id', 'region_woeid',
                'country_name', 'country_place_id', 'country_woeid', )
        }),
        ('EXIF', {
            'fields': ('exif_camera', 'exif_lens_model', 'exif_aperture', 'exif_exposure', 'exif_flash', 'exif_focal_length', 'exif_iso', )
        }),
        ('Data', {
            'fields': ('raw', 'sizes_raw', 'exif_raw', 'fetch_time', 'time_created', 'time_modified',)
        }),
    )
    readonly_fields = ('show_image', 'raw', 'fetch_time', 'time_created', 'time_modified',
        'sizes_raw', 'exif_raw', )

    formfield_overrides = {
        # Make the inputs full-width.
        models.CharField: {'widget': TextInput(
            attrs={
                'class': 'vLargeTextField',
            }
        )},
    }
    inlines = [TaggedPhotoInline,]
    raw_id_fields = ('user',)

    def show_thumb(self, instance):
        return '<img src="%s" width="%s" height="%s" />' % (instance.thumbnail_url, instance.width_t, instance.height_t)
    show_thumb.allow_tags = True
    show_thumb.short_description = ''

    def show_image(self, instance):
        return '<img src="%s" width="%s" height="%s" />' % (instance.medium_url, instance.width, instance.height)
    show_image.allow_tags = True
    show_image.short_description = 'Image'

