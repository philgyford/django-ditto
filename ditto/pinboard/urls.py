from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^$",
        view=views.HomeView.as_view(),
        name='home'
    ),
    url(
        regex=r"^to-read/$",
        view=views.ToreadListView.as_view(),
        name='toread'
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
        regex=r"^(?P<username>\w+)/$",
        view=views.AccountDetailView.as_view(),
        name='account_detail'
    ),
    url(
        regex=r"^(?P<username>\w+)/to-read/$",
        view=views.AccountToreadView.as_view(),
        name='account_toread'
    ),
    url(
        regex=r"^(?P<username>\w+)/tags/(?P<tag_slug>[^/]+)/$",
        view=views.AccountTagDetailView.as_view(),
        name='account_tag_detail'
    ),
    url(
        regex=r"^(?P<username>\w+)/(?P<hash>\w+)/$",
        view=views.BookmarkDetailView.as_view(),
        name='bookmark_detail'
    ),
]

