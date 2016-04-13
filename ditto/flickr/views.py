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
            context['accounts'] = Account.objects.all()
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

