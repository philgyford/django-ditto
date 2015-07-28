from django.conf.urls import url

from . import views

app_name = 'ditto'

urlpatterns = [
    url(
        regex=r"^$",
        view=views.Home.as_view(),
        name='index'
    ),
]

