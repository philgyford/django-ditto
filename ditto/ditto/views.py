from django.apps import apps
from django.views.generic import DetailView, TemplateView

from taggit.models import Tag

from ..pinboard.models import Bookmark


class Home(TemplateView):
    template_name = 'ditto/index.html'

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        if apps.is_installed('ditto.pinboard'):
            context['pinboard_bookmark_list'] = Bookmark.public_objects.all()[:5]
        return context


class TagDetail(DetailView):
    "All items with a certain tag"
    template_name = 'ditto/tag_detail.html'
    model = Tag

    def get_context_data(self, **kwargs):
        context = super(TagDetail, self).get_context_data(**kwargs)
        context['bookmark_list'] = Bookmark.public_objects.filter(tags__slug__in=[self.object.slug])
        return context

