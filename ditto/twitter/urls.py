from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^$",
        view=views.Home.as_view(),
        name='index'
    ),
    url(
        regex=r"^likes$",
        view=views.Favorites.as_view(),
        name='favorites'
    ),
    url(
        regex=r"^(?P<screen_name>\w+)$",
        view=views.UserDetail.as_view(),
        name='user_detail'
    ),
    url(
        regex=r"^(?P<screen_name>\w+)/likes$",
        view=views.AccountFavorites.as_view(),
        name='account_favorites'
    ),
    url(
        regex=r"^(?P<screen_name>\w+)/(?P<twitter_id>\d+)$",
        view=views.TweetDetail.as_view(),
        name='tweet_detail'
    ),
]

