from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^$",
        view=views.Home.as_view(),
        name='index'
    ),
    #url(
        #regex=r"^tags$",
        #view=views.TagList.as_view(),
        #name='tag_list'
    #),
    #url(
        #regex=r"^tags/(?P<slug>[^/]+)$",
        #view=views.TagDetail.as_view(),
        #name='tag_detail'
    #),
    url(
        # /2016/04/18/twitter/favorites
        regex=r"^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})(?:/(?P<app>[a-z]+))?(?:/(?P<variety>[a-z\-]+|))?$",
        view=views.DayArchive.as_view(),
        name='day_archive'
    ),
]

