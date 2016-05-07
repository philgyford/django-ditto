from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^$",
        view=views.HomeView.as_view(),
        name='home'
    ),
    url(
        regex=r"^likes/$",
        view=views.FavoriteListView.as_view(),
        name='favorite_list'
    ),
    url(
        regex=r"^(?P<screen_name>\w+)/$",
        view=views.UserDetailView.as_view(),
        name='user_detail'
    ),
    url(
        regex=r"^(?P<screen_name>\w+)/likes/$",
        view=views.AccountFavoriteListView.as_view(),
        name='account_favorite_list'
    ),
    url(
        regex=r"^(?P<screen_name>\w+)/(?P<twitter_id>\d+)/$",
        view=views.TweetDetailView.as_view(),
        name='tweet_detail'
    ),
]

