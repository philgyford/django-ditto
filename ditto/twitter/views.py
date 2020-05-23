from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin

from ..core.views import PaginatedListView
from .models import Account, Tweet, User


class HomeView(PaginatedListView):
    template_name = "twitter/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account_list"] = Account.objects.all()
        return context

    def get_queryset(self):
        "Get Tweets by all of the Accounts that have Users."
        # Use select_related to fetch user details too. Could be nasty...
        return Tweet.public_tweet_objects.all().prefetch_related("user")


class FavoriteListView(PaginatedListView):
    template_name = "twitter/favorite_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account_list"] = Account.objects.all()
        return context

    def get_queryset(self):
        "Get Tweets by all of the Accounts that have Users."
        return Tweet.public_favorite_objects.all().prefetch_related("user")


class SingleUserMixin(SingleObjectMixin):
    """Used for views that need data about a User based on screen_name in
    the URL, and its Account if it has one.
    """

    slug_field = "screen_name"
    slug_url_kwarg = "screen_name"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=User.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["twitter_user"] = self.object
        try:
            context["account"] = Account.objects.get(user=self.object)
        except Account.DoesNotExist:
            context["account"] = None
            context["public_accounts"] = Account.objects.filter(user__is_private=False)
        return context


class UserDetailView(SingleUserMixin, PaginatedListView):
    """A single Twitter User and its Tweets.
    The user might have an Account associated with it, or might not.
    """

    template_name = "twitter/user_detail.html"

    def get_queryset(self):
        "All public tweets from this Account."
        return Tweet.public_objects.filter(user=self.object).prefetch_related("user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tweet_list"] = context["object_list"]
        return context


class AccountFavoriteListView(SingleUserMixin, PaginatedListView):
    "A single Twitter User associated with an Account, and its Favorites."
    template_name = "twitter/account_favorite_list.html"

    def get_queryset(self):
        "All public favorites from this Account."
        return Tweet.public_favorite_objects.filter(
            favoriting_users__in=[self.object]
        ).prefetch_related("user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tweet_list"] = context["object_list"]
        return context


class TweetDetailView(DetailView):
    """Show a single tweet. It might be posted by one of the Accounts, or might
    be a tweet by someone else, favorited.
    """

    model = Tweet
    slug_field = "twitter_id"
    slug_url_kwarg = "twitter_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["twitter_user"] = context["tweet"].user
        if context["twitter_user"].is_private:
            # If private, we don't even send the Tweet to the template.
            context["tweet"] = None
        # We can show favorited tweets; they won't have an associated Account.
        try:
            context["account"] = Account.objects.get(user=context["twitter_user"])
        except Account.DoesNotExist:
            context["account"] = None
        return context
