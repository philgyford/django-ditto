from django.urls import path, re_path

from . import views


app_name = "flickr"

urlpatterns = [
    path("", view=views.HomeView.as_view(), name="home"),
    path("albums/", view=views.PhotosetListView.as_view(), name="photoset_list"),
    path("tags/", view=views.TagListView.as_view(), name="tag_list"),
    re_path(
        r"^tags/(?P<slug>[^/]+)/$",
        view=views.TagDetailView.as_view(),
        name="tag_detail",
    ),
    re_path(
        r"^(?P<nsid>[\dN@]+)/$",
        view=views.UserDetailView.as_view(),
        name="user_detail",
    ),
    re_path(
        r"^(?P<nsid>[\dN@]+)/albums/$",
        view=views.UserPhotosetListView.as_view(),
        name="user_photoset_list",
    ),
    re_path(
        r"^(?P<nsid>[\dN@]+)/albums/(?P<flickr_id>[^/]+)/$",
        view=views.PhotosetDetailView.as_view(),
        name="photoset_detail",
    ),
    re_path(
        r"^(?P<nsid>[\dN@]+)/tags/(?P<tag_slug>[^/]+)/$",
        view=views.UserTagDetailView.as_view(),
        name="user_tag_detail",
    ),
    re_path(
        r"^(?P<nsid>[\dN@]+)/(?P<flickr_id>\d+)/$",
        view=views.PhotoDetailView.as_view(),
        name="photo_detail",
    ),
]
