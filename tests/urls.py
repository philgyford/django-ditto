from django.urls import include, path

urlpatterns = [
    path("flickr/", include("ditto.flickr.urls", namespace="flickr")),
    path("lastfm/", include("ditto.lastfm.urls", namespace="lastfm")),
    path("pinboard/", include("ditto.pinboard.urls", namespace="pinboard")),
    path("twitter/", include("ditto.twitter.urls", namespace="twitter")),
    path("", include("ditto.core.urls", namespace="ditto")),
]
