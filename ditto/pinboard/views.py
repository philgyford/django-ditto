from django.http import Http404
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin

from taggit.models import Tag

from ..ditto.views import PaginatedListView
from .models import Account, Bookmark


class Home(PaginatedListView):
    "List all recent Bookmarks and all Accounts"
    template_name = 'pinboard/index.html'
    queryset = Bookmark.public_objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account_list'] = Account.objects.all()
        return context


class AccountDetail(SingleObjectMixin, PaginatedListView):
    "A single Pinboard Account and its Bookmarks."
    template_name = 'pinboard/account_detail.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Account.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = self.object
        context['bookmark_list'] = context['object_list']
        return context

    def get_queryset(self):
        "Show all the public Bookmarks associated with this account."
        return Bookmark.public_objects.filter(account=self.object)


class BookmarkDetail(DetailView):
    "A single Bookmark, from one Account"
    model = Bookmark
    # Only display public bookmarks; private ones will 404.
    queryset = Bookmark.public_objects.all()


class TagList(ListView):
    template_name = 'pinboard/tag_list.html'

    def get_queryset(self):
        return Bookmark.tags.most_common()


class TagDetail(SingleObjectMixin, PaginatedListView):
    "All Bookmarks with a certain tag from all Accounts"
    template_name = 'pinboard/tag_detail.html'
    allow_empty = False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Tag.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.object
        context['account_list'] = Account.objects.all()
        context['bookmark_list'] = context['object_list']
        return context

    def get_queryset(self):
        "Show all the public Bookmarks associated with this tag."
        return Bookmark.public_objects.filter(tags__slug__in=[self.object.slug])


class AccountTagDetail(SingleObjectMixin, PaginatedListView):
    "All Bookmarks with a certain Tag from one Account"
    template_name = 'pinboard/account_tag_detail.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    allow_empty = False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Account.objects.all())
        self.tag_object = self.get_tag_object()
        return super().get(request, *args, **kwargs)

    def get_tag_object(self):
        """Custom method for fetching the Tag."""
        try:
            obj = Tag.objects.get(slug=self.kwargs['tag_slug'])
        except Tag.DoesNotExist:
            raise Http404(_("No Tags found matching the query"))
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = self.object
        context['tag'] = self.tag_object
        context['bookmark_list'] = context['object_list']
        return context

    def get_queryset(self):
        """Show all the public Bookmarks associated with this account."""
        return Bookmark.public_objects.filter(account=self.object,
                                    tags__slug__in=[self.kwargs['tag_slug']])


