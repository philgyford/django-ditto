from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^$",
        view=views.Home.as_view(),
        name='index'
    ),
    url(
        regex=r"^tags$",
        view=views.TagList.as_view(),
        name='tag_list'
    ),
    url(
        regex=r"^tags/(?P<slug>[^/]+)$",
        view=views.TagDetail.as_view(),
        name='tag_detail'
    ),
    url(
        regex=r"^(?P<nsid>[\dN@]+)$",
        view=views.UserDetail.as_view(),
        name='user_detail'
    ),
    url(
        regex=r"^(?P<nsid>[\dN@]+)/tags/(?P<tag_slug>[^/]+)$",
        view=views.UserTagDetail.as_view(),
        name='user_tag_detail'
    ),
    url(
        regex=r"^(?P<nsid>[\dN@]+)/(?P<flickr_id>\d+)$",
        view=views.PhotoDetail.as_view(),
        name='photo_detail'
    ),
]
