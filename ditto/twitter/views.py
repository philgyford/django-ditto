from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin

from ..ditto.views import PaginatedListView
from .models import Account, Tweet, User


class Home(PaginatedListView):
    template_name = 'twitter/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account_list'] = Account.objects.all()
        return context

    def get_queryset(self):
        "Get Tweets by all of the Accounts that have Users."
        # Need to get the User for each Account that has one:
        accounts = Account.objects.exclude(user__isnull=True)
        user_ids = [account.user.id for account in accounts]
        users = User.objects.filter(pk__in=user_ids)

        # Use select_related to fetch user details too. Could be nasty...
        return Tweet.public_objects.filter(user=users).select_related().all()

class AccountDetail(SingleObjectMixin, PaginatedListView):
    "A single Twitter Account and its Tweets."
    template_name = 'twitter/account_detail.html'


class TweetDetail(DetailView):
    model = Tweet

