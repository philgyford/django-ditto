from django.http import Http404
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
    slug_field = 'screen_name'
    slug_url_kwarg = 'screen_name'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Account.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = self.object
        context['tweet_list'] = context['object_list']
        return context

    def get_object(self, queryset=None):
        "Get the Account that has the user with the screen_name from the URL"
        slug = self.kwargs.get(self.slug_url_kwarg)
        try:
            obj = Account.objects.get(user__screen_name=slug)
        except Account.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                      {'verbose_name': queryset.model._meta.verbose_name})
        return obj

    def get_queryset(self):
        "All public tweets from this Account."
        return Tweet.public_objects.filter(user=self.object.user)

class TweetDetail(DetailView):
    model = Tweet

