from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns("",
    url(
        regex=r"^$",
        view=views.Home.as_view(),
        name='pinboard'
    ),
    url(
        regex=r"^(?P<username>\w+)$",
        view=views.AccountDetail.as_view(),
        name='account_detail'
    ),
    url(
        regex=r"^(?P<username>\w+)/(?P<pk>\d+)$",
        view=views.BookmarkDetail.as_view(),
        name='bookmark_detail'
    )
)

