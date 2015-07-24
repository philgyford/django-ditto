from django.views.generic import TemplateView

from ..pinboard.models import Bookmark 


class Home(TemplateView):
    template_name = "ditto/ditto/index.html"

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        context['pinboard_bookmark_list'] = Bookmark.public_objects.all()[:5]
        return context
    

