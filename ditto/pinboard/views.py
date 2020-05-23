from django.http import Http404
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin

from ..core.views import PaginatedListView
from .models import Account, Bookmark, BookmarkTag


class SingleAccountMixin(SingleObjectMixin):
    "For views which list bookmarks and also need an Account object."
    slug_field = "username"
    slug_url_kwarg = "username"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Account.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account"] = self.object
        return context


class HomeView(PaginatedListView):
    "List all recent Bookmarks and all Accounts"
    template_name = "pinboard/home.html"
    queryset = Bookmark.public_objects.all().prefetch_related("account")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account_list"] = Account.objects.all()
        return context


class ToreadListView(PaginatedListView):
    template_name = "pinboard/toread_list.html"
    queryset = Bookmark.public_toread_objects.all().prefetch_related("account")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account_list"] = Account.objects.all()
        return context


class AccountDetailView(SingleAccountMixin, PaginatedListView):
    "A single Pinboard Account and its Bookmarks."
    template_name = "pinboard/account_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bookmark_list"] = context["object_list"]
        return context

    def get_queryset(self):
        "Show all the public Bookmarks associated with this account."
        return Bookmark.public_objects.filter(account=self.object).prefetch_related(
            "account"
        )


class AccountToreadView(SingleAccountMixin, PaginatedListView):
    "A single Pinboard Account and its 'to read' Bookmarks."
    template_name = "pinboard/account_toread.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bookmark_list"] = context["object_list"]
        return context

    def get_queryset(self):
        "Show all the public Bookmarks associated with this account."
        return Bookmark.public_toread_objects.filter(
            account=self.object
        ).prefetch_related("account")


class BookmarkDetailView(DetailView):
    "A single Bookmark, from one Account"
    model = Bookmark
    # Only display public bookmarks; private ones will 404.
    queryset = Bookmark.public_objects.all()
    slug_field = "url_hash"
    slug_url_kwarg = "hash"


class TagListView(ListView):
    template_name = "pinboard/tag_list.html"
    context_object_name = "tag_list"

    def get_queryset(self):
        return Bookmark.tags.most_common()[:100]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account_list"] = Account.objects.all()
        return context


class TagDetailView(SingleObjectMixin, PaginatedListView):
    "All Bookmarks with a certain tag from all Accounts"
    template_name = "pinboard/tag_detail.html"
    allow_empty = False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=BookmarkTag.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = self.object
        context["account_list"] = Account.objects.all()
        context["bookmark_list"] = context["object_list"]
        return context

    def get_queryset(self):
        "Show all the public Bookmarks associated with this tag."
        return Bookmark.public_objects.filter(
            tags__slug__in=[self.object.slug]
        ).prefetch_related("account")


class AccountTagDetailView(SingleAccountMixin, PaginatedListView):
    "All Bookmarks with a certain Tag from one Account"
    template_name = "pinboard/account_tag_detail.html"
    allow_empty = False

    def get(self, request, *args, **kwargs):
        self.tag_object = self.get_tag_object()
        return super().get(request, *args, **kwargs)

    def get_tag_object(self):
        """Custom method for fetching the Tag."""
        try:
            obj = BookmarkTag.objects.get(slug=self.kwargs["tag_slug"])
        except BookmarkTag.DoesNotExist:
            raise Http404(_("No Tags found matching the query"))
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = self.tag_object
        context["bookmark_list"] = context["object_list"]
        return context

    def get_queryset(self):
        """Show all the public Bookmarks associated with this account."""
        return Bookmark.public_objects.filter(
            account=self.object, tags__slug__in=[self.kwargs["tag_slug"]]
        )
