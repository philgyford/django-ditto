from datetime import timedelta

from django.http import Http404
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, TemplateView
from django.views.generic.detail import SingleObjectMixin

from ..core.utils import datetime_now
from ..core.views import PaginatedListView
from .models import Account, Album, Artist, Scrobble, Track


class AccountsMixin(object):
    """
    View Mixin for adding an `account_list` to context, with all Accounts in.
    And the total counts of Scrobbles, Albums, Artists and Tracks.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account_list"] = Account.objects.all()
        context["counts"] = {
            "albums": Album.objects.all().count(),
            "artists": Artist.objects.all().count(),
            "scrobbles": Scrobble.objects.all().count(),
            "tracks": Track.objects.all().count(),
        }
        return context


class HomeView(AccountsMixin, TemplateView):
    "Uses template tags to display charts, recent Scrobbles, etc."
    template_name = "lastfm/home.html"


class ScrobbleListView(AccountsMixin, PaginatedListView):
    "A multi-page list of Scrobbles, most recent first."
    template_name = "lastfm/scrobble_list.html"
    model = Scrobble

    def get_queryset(self):
        "Pre-fetch Artists and Tracks to reduce number of queries."
        qs = super(ScrobbleListView, self).get_queryset()
        return qs.prefetch_related("artist", "track")


class ChartPaginatedListView(PaginatedListView):
    """
    For the Album, Artist and Track ListViews that are charts ordered by
    scrobble_count.
    """

    ordering = "-scrobble_count"

    def get_queryset(self):
        return self.get_queryset_with_counts()

    def get_queryset_with_counts(self):
        """
        Includes scrobble_counts with returned objects, and adds ability to
        limit results to a time period based on the supplied `days`.

        This was just get_queryset(), but then combining this class with the
        SingleAccountMixin didn't work; child classes were using
        SingleObjectMixin's get_queryset().

        So now, each child class has to call this method from its own
        get_queryset().
        """
        queryset = self.model._default_manager

        # This will contain filters on the queryset:
        qs_kwargs = {}

        days = self.get_days()  # eg 7, 30 or 'all'

        if days != "all":
            time_ago = datetime_now() - timedelta(days=days)
            qs_kwargs["min_post_time"] = time_ago

        if hasattr(self, "object") and isinstance(self.object, Account):
            # We need to filter the results to only get Tracks (or whatever)
            # scrobbled by this Account.
            qs_kwargs["account"] = self.object

        queryset = queryset.with_scrobble_counts(**qs_kwargs)

        ordering = (self.get_ordering(),)
        queryset = queryset.order_by(*ordering)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_days"] = str(self.get_days())
        context["valid_days"] = self.get_valid_days()
        return context

    def get_valid_days(self):
        return [
            "7",
            "30",
            "90",
            "180",
            "365",
            "all",
        ]

    def get_days(self):
        """
        Returns the current number of recent days we're viewing.

        Returns an integer (number of days) or 'all'.
        """
        days = self.request.GET.get("days")
        if days and days in self.get_valid_days():
            try:
                return int(days)
            except ValueError:
                return days
        else:
            return "all"


class AlbumListView(AccountsMixin, ChartPaginatedListView):
    "A multi-page chart of most-scrobbled Tracks."
    template_name = "lastfm/album_list.html"
    model = Album


class ArtistListView(AccountsMixin, ChartPaginatedListView):
    "A multi-page chart of most-scrobbled Tracks."
    template_name = "lastfm/artist_list.html"
    model = Artist


class TrackListView(AccountsMixin, ChartPaginatedListView):
    "A multi-page chart of most-scrobbled Tracks."
    template_name = "lastfm/track_list.html"
    model = Track


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

        artist_slug = self.kwargs.get("artist_slug")
        album_slug = self.kwargs.get("album_slug")

        if artist_slug is None or album_slug is None:
            raise AttributeError(
                "AlbumDetailView must be called with " "artist_slug and album_slug"
            )

        artist = Artist.objects.get(slug=artist_slug)
        queryset = queryset.filter(artist=artist, slug=album_slug)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )
        return obj


class ArtistDetailView(DetailView):
    "One Artist. Uses a template tag to display a chart of their Tracks."
    model = Artist
    slug_url_kwarg = "artist_slug"


class ArtistAlbumsView(DetailView):
    "One Artist. Uses a template tag to display a chart of their Albums."
    model = Artist
    slug_url_kwarg = "artist_slug"
    template_name = "lastfm/artist_albums.html"


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

        artist_slug = self.kwargs.get("artist_slug")
        track_slug = self.kwargs.get("track_slug")

        if artist_slug is None or track_slug is None:
            raise AttributeError(
                "TrackDetailView must be called with " "artist_slug and track_slug"
            )

        artist = Artist.objects.get(slug=artist_slug)
        queryset = queryset.filter(artist=artist, slug=track_slug)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )
        return obj


class SingleAccountMixin(SingleObjectMixin):
    """Used for views that need data about an Account based on username in
    the URL.
    """

    slug_field = "username"
    slug_url_kwarg = "username"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Account.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        "Add counts of things for this Account only."
        context = super().get_context_data(**kwargs)

        qs = Scrobble.objects.filter(account=self.object)

        context["counts"] = {
            "albums": qs.exclude(album_id__isnull=True)
            .values("album_id")
            .distinct()
            .count(),
            "artists": qs.values("artist_id").distinct().count(),
            "scrobbles": qs.count(),
            "tracks": qs.values("track_id").distinct().count(),
        }
        return context


class UserDetailView(SingleAccountMixin, DetailView):
    "Overview of the user; top 10s of everything."
    template_name = "lastfm/user_detail.html"
    model = Account


class UserAlbumListView(SingleAccountMixin, ChartPaginatedListView):
    "Chart of Albums scrobbled by one user."
    template_name = "lastfm/user_album_list.html"
    model = Album

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["album_list"] = context["object_list"]
        return context

    def get_queryset(self):
        return self.get_queryset_with_counts()


class UserArtistListView(SingleAccountMixin, ChartPaginatedListView):
    "Chart of Artists scrobbled by one user."
    template_name = "lastfm/user_artist_list.html"
    model = Artist

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["artist_list"] = context["object_list"]
        return context

    def get_queryset(self):
        return self.get_queryset_with_counts()


class UserScrobbleListView(SingleAccountMixin, PaginatedListView):
    "All scrobbles by one user."
    template_name = "lastfm/user_scrobble_list.html"
    model = Scrobble

    def get_queryset(self):
        """
        All Scrobbles by this Account.
        And pre-fetch Artists and Tracks to reduce number of queries.
        """
        queryset = super().get_queryset()
        return queryset.filter(account=self.object).prefetch_related("artist", "track")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["scrobble_list"] = context["object_list"]
        return context


class UserTrackListView(SingleAccountMixin, ChartPaginatedListView):
    "Chart of Tracks scrobbled by one user."
    template_name = "lastfm/user_track_list.html"
    model = Track

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["track_list"] = context["object_list"]
        return context

    def get_queryset(self):
        return self.get_queryset_with_counts()
