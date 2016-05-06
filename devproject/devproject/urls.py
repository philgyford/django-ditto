from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),

    url(r'^flickr/', include('ditto.flickr.urls', namespace='flickr')),
    url(r'^pinboard/', include('ditto.pinboard.urls', namespace='pinboard')),
    url(r'^twitter/', include('ditto.twitter.urls', namespace='twitter')),
    url(r'', include('ditto.core.urls', namespace='ditto')),
]


from django.conf import settings
from django.conf.urls import include, patterns, url

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
