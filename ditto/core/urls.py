from django.urls import path, re_path

from . import views


app_name = "ditto"

urlpatterns = [
    path("", view=views.HomeView.as_view(), name="home"),
    # path(
    # "tags",
    # view=views.TagListView.as_view(),
    # name='tag_list'
    # ),
    # re_path(
    # r"^tags/(?P<slug>[^/]+)$",
    # view=views.TagDetailView.as_view(),
    # name='tag_detail'
    # ),
    re_path(
        # /2016/04/18/twitter/favorites
        r"^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})(?:/(?P<app>[a-z]+))?(?:/(?P<variety>[a-z\/]+|))?$",  # noqa: E501
        view=views.DayArchiveView.as_view(),
        name="day_archive",
    ),
]
