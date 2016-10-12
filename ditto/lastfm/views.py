from django.db import models
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, TemplateView
from django.views.generic.detail import SingleObjectMixin

from ..core.views import PaginatedListView
from .models import Account, Album, Artist, Scrobble, Track


class AccountsMixin(object):
    """
    View Mixin for adding an `account_list` to context, with all Accounts in.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account_list'] = Account.objects.all()
        return context


class HomeView(AccountsMixin, TemplateView):
    "Uses template tags to display charts, recent Scrobbles, etc."
    template_name = 'lastfm/home.html'


class ScrobbleListView(AccountsMixin, PaginatedListView):
    "A multi-page list of Scrobbles, most recent first."
    template_name = 'lastfm/scrobble_list.html'
    model = Scrobble


class TrackListView(AccountsMixin, PaginatedListView):
    "A multi-page chart of most-scrobbled Tracks."
    template_name = 'lastfm/track_list.html'
    model = Track
    ordering = '-scrobble_count'

    def get_queryset(self):
        "Basic version of ListView.get_queryset()"
        queryset = self.model._default_manager.with_scrobble_counts()
        ordering = (self.get_ordering(),)
        queryset = queryset.order_by(*ordering)
        return queryset


class AlbumListView(AccountsMixin, PaginatedListView):
    "A multi-page chart of most-scrobbled Tracks."
    template_name = 'lastfm/album_list.html'
    model = Album
    ordering = '-scrobble_count'

    def get_queryset(self):
        "Basic version of ListView.get_queryset()"
        queryset = self.model._default_manager.with_scrobble_counts()
        ordering = (self.get_ordering(),)
        queryset = queryset.order_by(*ordering)
        return queryset


class AlbumDetailView(DetailView):
    "A single Album by a particular Artist."
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
    "One Artist. Uses a template tag to display a chart of their Tracks."
    model = Artist
    slug_url_kwarg = 'artist_slug'


class ArtistAlbumsView(DetailView):
    "One Artist. Uses a template tag to display a chart of their Albums."
    model = Artist
    slug_url_kwarg = 'artist_slug'
    template_name = 'lastfm/artist_albums.html'


class TrackDetailView(DetailView):
    "One Track by a particular Artist."
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
    " TODO "
    slug_field = 'username'
    slug_url_kwarg = 'username'

    queryset = Scrobble.objects

