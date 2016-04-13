from django.http import Http404
from django.utils.translation import ugettext as _
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin

from ..ditto.views import PaginatedListView
from .models import Account, Photo, User


class Home(PaginatedListView):
    template_name = 'flickr/index.html'
    paginate_by = 48

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account_list'] = Account.objects.all()
        return context

    def get_queryset(self):
        "Get Photos by all of the Accounts that have Users."
        # Use select_related to fetch user details too. Could be nasty...
        return Photo.public_photo_objects.all().select_related()


class UserDetailMixin(SingleObjectMixin):
    """Used for views that need data about a User based on nsid in
    the URL, and its Account if it has one.
    """
    slug_field = 'nsid'
    slug_url_kwarg = 'nsid'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=User.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['flickr_user'] = self.object
        try:
            context['account'] = Account.objects.get(user=self.object)
        except Account.DoesNotExist:
            context['account'] = None
        return context


class UserDetail(UserDetailMixin, PaginatedListView):
    """A single Flickr User and its Photos.
    The user might have an Account associated with it, or might not.
    """
    template_name = 'flickr/user_detail.html'
    paginate_by = 48

    def get_queryset(self):
        "All public Photos from this Account."
        return Photo.public_objects.filter(user=self.object).select_related()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photo_list'] = context['object_list']
        return context


class PhotoDetail(DetailView):
    """Show a single Photo. It might be posted by one of the Accounts, or might
    be a Photo by someone else, favorited.
    """
    model = Photo
    slug_field = 'flickr_id'
    slug_url_kwarg = 'flickr_id'

    def get_object(self, queryset=None):
        """Do standard DetailView.get_object(), but return 404 if the Photo is
        private."""
        obj = super().get_object(queryset)
        if obj.is_private:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                                      {'verbose_name': obj._meta.verbose_name})
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['flickr_user'] = context['photo'].user
        # We can show favorited Photos; they won't have an associated Account.
        try:
            context['account'] = Account.objects.get(
                                                user=context['flickr_user'])
        except Account.DoesNotExist:
            context['account'] = None
        return context

