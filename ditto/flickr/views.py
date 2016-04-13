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

