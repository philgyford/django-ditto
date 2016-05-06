from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^$",
        view=views.Home.as_view(),
        name='home'
    ),
    url(
        regex=r"^likes/$",
        view=views.FavoriteList.as_view(),
        name='favorite_list'
    ),
    url(
        regex=r"^(?P<screen_name>\w+)/$",
        view=views.UserDetail.as_view(),
        name='user_detail'
    ),
    url(
        regex=r"^(?P<screen_name>\w+)/likes/$",
        view=views.AccountFavoriteList.as_view(),
        name='account_favorite_list'
    ),
    url(
        regex=r"^(?P<screen_name>\w+)/(?P<twitter_id>\d+)/$",
        view=views.TweetDetail.as_view(),
        name='tweet_detail'
    ),
]

