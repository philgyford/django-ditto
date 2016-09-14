from django.contrib import admin

from .models import Account, Album, Artist, Scrobble, Track


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'realname', 'is_active', 'time_created',)

    fieldsets = (
        (None, {
            'fields': ('username', 'realname', 'api_key', 'is_active', )
        }),
        ('Data', {
            'fields': ('time_created', 'time_modified',)
        }),
    )

    readonly_fields = ('time_created', 'time_modified',)


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'mbid', 'time_created',)

    fieldsets = (
        (None, {
            'fields': ('name', 'mbid',)
        }),
        ('Data', {
            'fields': ('time_created', 'time_modified',)
        }),
    )

    readonly_fields = ('time_created', 'time_modified',)


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('name', 'artist', 'mbid', 'time_created',)

    fieldsets = (
        (None, {
            'fields': ('name', 'artist', 'mbid',)
        }),
        ('Data', {
            'fields': ('time_created', 'time_modified',)
        }),
    )

    raw_id_fields = ('artist',)
    readonly_fields = ('time_created', 'time_modified',)


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('name', 'artist', 'mbid', 'time_created',)

    fieldsets = (
        (None, {
            'fields': ('name', 'artist', 'mbid',)
        }),
        ('Data', {
            'fields': ('time_created', 'time_modified',)
        }),
    )

    raw_id_fields = ('artist',)
    readonly_fields = ('time_created', 'time_modified',)


@admin.register(Scrobble)
class ScrobbleAdmin(admin.ModelAdmin):
    list_display = ('artist_and_name', 'post_time',)

    fieldsets = (
        (None, {
            'fields': ('account',
                        'artist', 'artist_name', 'artist_mbid',
                        'track', 'track_name', 'track_mbid',
                        'album', 'album_name', 'album_mbid',
                        'post_time',)
        }),
        ('Data', {
            'fields': ('raw', 'fetch_time', 'time_created', 'time_modified',)
        }),
    )

    raw_id_fields = ('artist', 'track', 'album',)
    readonly_fields = ('raw', 'fetch_time', 'time_created', 'time_modified',)

    def artist_and_name(self, instance):
        return '%s - %s' % (instance.artist_name, instance.track_name)

