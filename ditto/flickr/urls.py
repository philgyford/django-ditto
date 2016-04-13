from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^$",
        view=views.Home.as_view(),
        name='index'
    ),
    url(
        regex=r"^(?P<nsid>[\dN@]+)$",
        view=views.UserDetail.as_view(),
        name='user_detail'
    ),
]
