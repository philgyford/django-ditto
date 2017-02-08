from django.conf.urls import url

from . import views


# The pattern for matching an Album/Artist/Track slug:
slug_chars = '[\w.,:;=@&+%()$!°’~-]+'


urlpatterns = [
    url(
        regex=r"^$",
        view=views.HomeView.as_view(),
        name='home'
    ),
    url(
        regex=r"^library/$",
        view=views.ScrobbleListView.as_view(),
        name='scrobble_list'
    ),
    url(
        regex=r"^library/albums/$",
        view=views.AlbumListView.as_view(),
        name='album_list'
    ),
    url(
        regex=r"^library/artists/$",
        view=views.ArtistListView.as_view(),
        name='artist_list'
    ),
    url(
        regex=r"^library/tracks/$",
        view=views.TrackListView.as_view(),
        name='track_list'
    ),
    url(
        regex=r"^music/(?P<artist_slug>%s)/$" % slug_chars,
        view=views.ArtistDetailView.as_view(),
        name='artist_detail'
    ),
    url(
        regex=r"^music/(?P<artist_slug>%s)/\+albums/$" % slug_chars,
        view=views.ArtistAlbumsView.as_view(),
        name='artist_albums'
    ),
    url(
        regex=r"^music/(?P<artist_slug>%s)/(?P<album_slug>%s)/$" % (
                                                    slug_chars, slug_chars),
        view=views.AlbumDetailView.as_view(),
        name='album_detail'
    ),
    url(
        regex=r"^music/(?P<artist_slug>%s)/_/(?P<track_slug>%s)/$" % (
                                                    slug_chars, slug_chars),
        view=views.TrackDetailView.as_view(),
        name='track_detail'
    ),

    # User pages.

    url(
        regex=r"^user/(?P<username>[a-z0-9]+)/$",
        view=views.UserDetailView.as_view(),
        name='user_detail'
    ),
    url(
        regex=r"^user/(?P<username>[a-z0-9]+)/library/$",
        view=views.UserScrobbleListView.as_view(),
        name='user_scrobble_list'
    ),
    url(
        regex=r"^user/(?P<username>[a-z0-9]+)/library/albums/$",
        view=views.UserAlbumListView.as_view(),
        name='user_album_list'
    ),
    url(
        regex=r"^user/(?P<username>[a-z0-9]+)/library/artists/$",
        view=views.UserArtistListView.as_view(),
        name='user_artist_list'
    ),
    url(
        regex=r"^user/(?P<username>[a-z0-9]+)/library/tracks/$",
        view=views.UserTrackListView.as_view(),
        name='user_track_list'
    ),
]
