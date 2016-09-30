from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        regex=r"^$",
        view=views.HomeView.as_view(),
        name='home'
    ),
    url(
        regex=r"^album/(?P<id>[^/]+)/$",
        view=views.AlbumDetailView.as_view(),
        name='album_detail'
    ),
    url(
        regex=r"^artist/(?P<id>[^/]+)/$",
        view=views.ArtistDetailView.as_view(),
        name='artist_detail'
    ),
    url(
        regex=r"^track/(?P<id>[^/]+)/$",
        view=views.TrackDetailView.as_view(),
        name='track_detail'
    ),
    url(
        regex=r"^(?P<username>[a-z]+)/$",
        view=views.UserDetailView.as_view(),
        name='user_detail'
    ),
]
