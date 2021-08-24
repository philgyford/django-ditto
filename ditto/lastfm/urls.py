from django.urls import path, re_path

from . import views


app_name = "lastfm"


# The pattern for matching an Album/Artist/Track slug:
slug_chars = r"[\w.,:;=@&+%()$!°’~-]+"  # noqa: W605


urlpatterns = [
    path("", view=views.HomeView.as_view(), name="home"),
    path("library/", view=views.ScrobbleListView.as_view(), name="scrobble_list"),
    path(
        "library/albums/",
        view=views.AlbumListView.as_view(),
        name="album_list",
    ),
    path(
        "library/artists/",
        view=views.ArtistListView.as_view(),
        name="artist_list",
    ),
    path(
        "library/tracks/",
        view=views.TrackListView.as_view(),
        name="track_list",
    ),
    re_path(
        r"^music/(?P<artist_slug>%s)/$" % slug_chars,
        view=views.ArtistDetailView.as_view(),
        name="artist_detail",
    ),
    re_path(
        r"^music/(?P<artist_slug>%s)/\+albums/$" % slug_chars,
        view=views.ArtistAlbumsView.as_view(),
        name="artist_albums",
    ),
    re_path(
        r"^music/(?P<artist_slug>%s)/(?P<album_slug>%s)/$" % (slug_chars, slug_chars),
        view=views.AlbumDetailView.as_view(),
        name="album_detail",
    ),
    re_path(
        r"^music/(?P<artist_slug>%s)/_/(?P<track_slug>%s)/$" % (slug_chars, slug_chars),
        view=views.TrackDetailView.as_view(),
        name="track_detail",
    ),
    # User pages.
    re_path(
        r"^user/(?P<username>[a-z0-9]+)/$",
        view=views.UserDetailView.as_view(),
        name="user_detail",
    ),
    re_path(
        r"^user/(?P<username>[a-z0-9]+)/library/$",
        view=views.UserScrobbleListView.as_view(),
        name="user_scrobble_list",
    ),
    re_path(
        r"^user/(?P<username>[a-z0-9]+)/library/albums/$",
        view=views.UserAlbumListView.as_view(),
        name="user_album_list",
    ),
    re_path(
        r"^user/(?P<username>[a-z0-9]+)/library/artists/$",
        view=views.UserArtistListView.as_view(),
        name="user_artist_list",
    ),
    re_path(
        r"^user/(?P<username>[a-z0-9]+)/library/tracks/$",
        view=views.UserTrackListView.as_view(),
        name="user_track_list",
    ),
]
