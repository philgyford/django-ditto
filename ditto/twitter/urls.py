from django.urls import path, re_path

from . import views


app_name = "twitter"

urlpatterns = [
    path("", view=views.HomeView.as_view(), name="home"),
    path("likes/", view=views.FavoriteListView.as_view(), name="favorite_list"),
    re_path(
        r"^(?P<screen_name>\w+)/$",
        view=views.UserDetailView.as_view(),
        name="user_detail",
    ),
    re_path(
        r"^(?P<screen_name>\w+)/likes/$",
        view=views.AccountFavoriteListView.as_view(),
        name="account_favorite_list",
    ),
    re_path(
        r"^(?P<screen_name>\w+)/(?P<twitter_id>\d+)/$",
        view=views.TweetDetailView.as_view(),
        name="tweet_detail",
    ),
]
