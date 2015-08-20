from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^$",
        view=views.Home.as_view(),
        name='index'
    ),
    url(
        regex=r"^(?P<username>\w+)$",
        view=views.AccountDetail.as_view(),
        name='account_detail'
    ),
    url(
        regex=r"^(?P<username>\w+)/(?P<twitter_id>\d+)$",
        view=views.TweetDetail.as_view(),
        name='tweet_detail'
    ),
]

