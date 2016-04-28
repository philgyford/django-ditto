from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^$",
        view=views.Home.as_view(),
        name='index'
    ),
    url(
        regex=r"^to-read/$",
        view=views.ToreadList.as_view(),
        name='toread'
    ),
    url(
        regex=r"^tags/$",
        view=views.TagList.as_view(),
        name='tag_list'
    ),
    url(
        regex=r"^tags/(?P<slug>[^/]+)/$",
        view=views.TagDetail.as_view(),
        name='tag_detail'
    ),
    url(
        regex=r"^(?P<username>\w+)/$",
        view=views.AccountDetail.as_view(),
        name='account_detail'
    ),
    url(
        regex=r"^(?P<username>\w+)/to-read/$",
        view=views.AccountToread.as_view(),
        name='account_toread'
    ),
    url(
        regex=r"^(?P<username>\w+)/tags/(?P<tag_slug>[^/]+)/$",
        view=views.AccountTagDetail.as_view(),
        name='account_tag_detail'
    ),
    url(
        regex=r"^(?P<username>\w+)/(?P<hash>\w+)/$",
        view=views.BookmarkDetail.as_view(),
        name='bookmark_detail'
    ),
]

