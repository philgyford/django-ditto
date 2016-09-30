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


class OptionalMbidDetailView(DetailView):
    """
    Extension of DetailView that allows us to look up an item by either an
    MBID or a Django PK.
    Expects an `id` from the URL.
    If that looks like an MBID, we use that.
    Otherwise, we try it as a Django PK.
    """

    def id_is_mbid(self, id):
        "For testing if an ID from a URL is an MBID or a Django PK"
        if '-' in id:
            return True
        else:
            return False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # If we've come here with the PK, but the object actually has an MBID,
        # redirect to the same page but using that:
        if not self.id_is_mbid(self.kwargs.get('id')) and self.object.mbid:
            return redirect('lastfm:%s' % request.resolver_match.url_name,
                            id=self.object.mbid)

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.
        This requires `self.queryset` and an `id` argument in the URLconf.

        Mostly from DetailView.get_object() with our modification for checking
        whether we're using a Django PK or an MBID.
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        # Our modification:
        id = self.kwargs.get('id')
        if id is not None:
            if self.id_is_mbid(id):
                queryset = queryset.filter(mbid=id)
            else:
                queryset = queryset.filter(pk=id)
        else:
            raise AttributeError("This detail view %s must be called with "
                                 "an id."
                                 % self.__class__.__name__)
        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj


class AlbumDetailView(OptionalMbidDetailView):
    model = Album


class ArtistDetailView(OptionalMbidDetailView):
    model = Artist


class TrackDetailView(OptionalMbidDetailView):
    model = Track


class UserDetailView(SingleObjectMixin, PaginatedListView):
    slug_field = 'username'
    slug_url_kwarg = 'username'

    queryset = Scrobble.objects

