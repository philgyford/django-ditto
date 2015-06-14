from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns("",
    url(
        regex=r"^$",
        view=views.PinboardHomeView.as_view(),
        name='pinboard_home'
    ),
)

