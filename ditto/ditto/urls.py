from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^$",
        view=views.Home.as_view(),
        name='index'
    ),
    url(
        regex=r"^tags$",
        view=views.TagList.as_view(),
        name='tag_list'
    ),
    url(
        regex=r"^tags/(?P<slug>[-_\w]+)$",
        view=views.TagDetail.as_view(),
        name='tag_detail'
    ),
]

