from ..ditto.paginator import DiggPaginator

from django.views.generic import DetailView, ListView

from . import models


class HomeView(ListView):
    model = models.Bookmark
    paginator_class = DiggPaginator
    paginate_by = 50
    page_kwarg = 'p'

class BookmarkDetailView(DetailView):
    model = models.Bookmark

