from django.http import Http404
from django.shortcuts import get_object_or_404
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
        # Use select_related to fetch user details too. Could be nasty...
        return Tweet.public_tweet_objects.all().select_related()


class Favorites(PaginatedListView):
    template_name = 'twitter/favorites.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account_list'] = Account.objects.all()
        return context

    def get_queryset(self):
        "Get Tweets by all of the Accounts that have Users."
        return Tweet.public_favorite_objects.all().select_related()


class AccountDetailMixin(SingleObjectMixin):
    """Used for views that need data about an Account based on screen_name in
    the URL, and a list of some tweets.
    """
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
        return get_object_or_404(Account, user__screen_name=slug)


class AccountDetail(AccountDetailMixin, PaginatedListView):
    "A single Twitter Account and its Tweets."
    template_name = 'twitter/account_detail.html'

    def get_queryset(self):
        "All public tweets from this Account."
        return Tweet.public_objects.filter(
                                        user=self.object.user).select_related()


class AccountFavorites(AccountDetailMixin, PaginatedListView):
    "A single Twitter Account and its Favorites."
    template_name = 'twitter/account_favorites.html'

    def get_queryset(self):
        "All public favorites from this Account."
        return Tweet.public_favorite_objects.filter(
                    favoriting_users__in=[self.object.user]).select_related()


class TweetDetail(DetailView):
    """Show a single tweet. It might be posted by one of the Accounts, or might
    be a tweet by someone else, favorited.
    """
    model = Tweet
    slug_field = 'twitter_id'
    slug_url_kwarg = 'twitter_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['twitter_user'] = context['tweet'].user
        if context['twitter_user'].is_private:
            # If private, we don't even send the Tweet to the template.
            context['tweet'] = None
        # We can show favorited tweets; they won't have an associated Account.
        try:
            context['account'] = Account.objects.get(
                                                user=context['twitter_user'])
        except Account.DoesNotExist:
            context['account'] = None
        return context

