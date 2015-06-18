from django.views.generic import DetailView, ListView

from . import models


class HomeView(ListView):
    model = models.Bookmark
    #template_name = "ditto/pinboard/index.html"


class BookmarkDetailView(DetailView):
    model = models.Bookmark
    #template_name = "ditto/pinboard/bookmark_detail.html"

