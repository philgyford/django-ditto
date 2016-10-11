from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin

from ..core.views import PaginatedListView
from .models import Account, Album, Artist, Scrobble, Track


class HomeView(PaginatedListView):
    template_name = 'lastfm/home.html'
    model = Scrobble

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account_list'] = Account.objects.all()
        return context


class AlbumDetailView(DetailView):
    model = Album

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.

        This is based on DetailView's method.
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        artist_slug = self.kwargs.get('artist_slug')
        album_slug = self.kwargs.get('album_slug')

        if artist_slug is None or album_slug is None:
            raise AttributeError("AlbumDetailView must be called with "
                     "artist_slug and album_slug")

        artist = Artist.objects.get(slug=artist_slug)
        queryset = queryset.filter(artist=artist, slug=album_slug)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj


class ArtistDetailView(DetailView):
    model = Artist
    slug_url_kwarg = 'artist_slug'


class TrackDetailView(DetailView):
    model = Track

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.

        This is based on DetailView's method.
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        artist_slug = self.kwargs.get('artist_slug')
        track_slug = self.kwargs.get('track_slug')

        if artist_slug is None or track_slug is None:
            raise AttributeError("TrackDetailView must be called with "
                     "artist_slug and track_slug")

        artist = Artist.objects.get(slug=artist_slug)
        queryset = queryset.filter(artist=artist, slug=track_slug)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj


class UserDetailView(SingleObjectMixin, PaginatedListView):
    slug_field = 'username'
    slug_url_kwarg = 'username'

    queryset = Scrobble.objects

