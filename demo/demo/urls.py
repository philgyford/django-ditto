from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),

    url(r'^pinboard/', include('ditto.pinboard.urls', namespace='pinboard')),
    url(r'', include('ditto.ditto.urls', namespace='ditto')),
]
