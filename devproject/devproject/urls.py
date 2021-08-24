from django.conf import settings
from django.conf.urls import static
from django.urls import include, path, re_path
from django.contrib import admin


urlpatterns = [
    path(r"admin/", admin.site.urls),
    path(r"flickr/", include("ditto.flickr.urls")),
    path(r"lastfm/", include("ditto.lastfm.urls")),
    path(r"pinboard/", include("ditto.pinboard.urls")),
    path(r"twitter/", include("ditto.twitter.urls")),
    path(r"", include("ditto.core.urls")),
]


if settings.DEBUG:

    import debug_toolbar

    urlpatterns += [
        re_path(r"^__debug__/", include(debug_toolbar.urls)),
    ]

    urlpatterns += static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += static.static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
