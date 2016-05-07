from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^$",
        view=views.HomeView.as_view(),
        name='home'
    ),
    url(
        regex=r"^albums/$",
        view=views.PhotosetListView.as_view(),
        name='photoset_list'
    ),
    url(
        regex=r"^tags/$",
        view=views.TagListView.as_view(),
        name='tag_list'
    ),
    url(
        regex=r"^tags/(?P<slug>[^/]+)/$",
        view=views.TagDetailView.as_view(),
        name='tag_detail'
    ),
    url(
        regex=r"^(?P<nsid>[\dN@]+)/$",
        view=views.UserDetailView.as_view(),
        name='user_detail'
    ),
    url(
        regex=r"^(?P<nsid>[\dN@]+)/albums/$",
        view=views.UserPhotosetListView.as_view(),
        name='user_photoset_list'
    ),
    url(
        regex=r"^(?P<nsid>[\dN@]+)/albums/(?P<flickr_id>[^/]+)/$",
        view=views.PhotosetDetailView.as_view(),
        name='photoset_detail'
    ),
    url(
        regex=r"^(?P<nsid>[\dN@]+)/tags/(?P<tag_slug>[^/]+)/$",
        view=views.UserTagDetailView.as_view(),
        name='user_tag_detail'
    ),
    url(
        regex=r"^(?P<nsid>[\dN@]+)/(?P<flickr_id>\d+)/$",
        view=views.PhotoDetailView.as_view(),
        name='photo_detail'
    ),
]
