from django.conf.urls import include, url

urlpatterns = [
    url(r'^flickr/', include('ditto.flickr.urls', namespace='flickr')),
    url(r'^pinboard/', include('ditto.pinboard.urls', namespace='pinboard')),
    url(r'^twitter/', include('ditto.twitter.urls', namespace='twitter')),
    url(r'', include('ditto.core.urls', namespace='ditto')),
]
