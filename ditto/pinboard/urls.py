from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns("",
    url(
        regex=r"^$",
        view=views.HomeView.as_view(),
        name='pinboard'
    ),
    url(
        regex=r"^(?P<username>\w+)/(?P<pk>\d+)$",
        view=views.BookmarkDetailView.as_view(),
        name='bookmark_detail'
    )
)

