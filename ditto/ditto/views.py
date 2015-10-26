from django.apps import apps
from django.views.generic import DetailView, ListView, TemplateView

from .paginator import DiggPaginator

if apps.is_installed('ditto.pinboard'):
    from ..pinboard.models import Bookmark

if apps.is_installed('ditto.twitter'):
    from ..twitter.models import Tweet


class PaginatedListView(ListView):
    """Use this instead of ListView to provide standardised pagination."""
    paginator_class = DiggPaginator
    paginate_by = 50
    page_kwarg = 'p'

    def __init__(self, **kwargs):
        return super().__init__(**kwargs)


class Home(TemplateView):
    template_name = 'ditto/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if apps.is_installed('ditto.pinboard'):
            context['pinboard_bookmark_list'] = Bookmark.public_objects.all()[:5]
        if apps.is_installed('ditto.twitter'):
            context['twitter_recent_tweet_list'] = Tweet.public_objects.all().select_related()[:5]
            context['twitter_favorites_tweet_list'] = Tweet.public_favorite_objects.all().select_related()[:5]
        return context


class TagList(TemplateView):
    "Doesn't really do anything at the moment."
    template_name = 'ditto/tag_list.html'


class TagDetail(TemplateView):
    "All items with a certain tag"
    template_name = 'ditto/tag_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = kwargs['slug']
        if apps.is_installed('ditto.pinboard'):
            context['bookmark_list'] = Bookmark.public_objects.filter(
                                            tags__slug__in=[kwargs['slug']])
        return context

