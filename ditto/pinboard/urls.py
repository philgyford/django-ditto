from django.urls import path, re_path

from . import views


app_name = "pinboard"

urlpatterns = [
    path("", view=views.HomeView.as_view(), name="home"),
    path("to-read/", view=views.ToreadListView.as_view(), name="toread"),
    path("tags/", view=views.TagListView.as_view(), name="tag_list"),
    re_path(
        r"^tags/(?P<slug>[^/]+)/$",
        view=views.TagDetailView.as_view(),
        name="tag_detail",
    ),
    re_path(
        r"^(?P<username>\w+)/$",
        view=views.AccountDetailView.as_view(),
        name="account_detail",
    ),
    re_path(
        r"^(?P<username>\w+)/to-read/$",
        view=views.AccountToreadView.as_view(),
        name="account_toread",
    ),
    re_path(
        r"^(?P<username>\w+)/tags/(?P<tag_slug>[^/]+)/$",
        view=views.AccountTagDetailView.as_view(),
        name="account_tag_detail",
    ),
    re_path(
        r"^(?P<username>\w+)/(?P<hash>\w+)/$",
        view=views.BookmarkDetailView.as_view(),
        name="bookmark_detail",
    ),
]
