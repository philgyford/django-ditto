from django.conf.urls import include, static, url
from django.contrib import admin


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^flickr/', include('ditto.flickr.urls')),
    url(r'^lastfm/', include('ditto.lastfm.urls')),
    url(r'^pinboard/', include('ditto.pinboard.urls')),
    url(r'^twitter/', include('ditto.twitter.urls')),
    url(r'', include('ditto.core.urls')),
]


from django.conf import settings

if settings.DEBUG:

    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

    urlpatterns += \
        static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += \
        static.static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
