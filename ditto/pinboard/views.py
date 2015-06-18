from django.views.generic import DetailView, ListView

from . import models


class HomeView(ListView):
    model = models.Bookmark

class BookmarkDetailView(DetailView):
    model = models.Bookmark

