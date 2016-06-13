from django.conf.urls import include, static, url
from django.contrib import admin


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),

    url(r'^flickr/', include('ditto.flickr.urls', namespace='flickr')),
    url(r'^pinboard/', include('ditto.pinboard.urls', namespace='pinboard')),
    url(r'^twitter/', include('ditto.twitter.urls', namespace='twitter')),
    url(r'', include('ditto.core.urls', namespace='ditto')),
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
