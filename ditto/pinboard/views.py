from ..ditto.paginator import DiggPaginator

from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin

from .models import Account, Bookmark


class Home(ListView):
    model = Bookmark
    paginator_class = DiggPaginator
    paginate_by = 50
    page_kwarg = 'p'

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        context['account_list'] = Account.objects.all()
        return context


class AccountDetail(SingleObjectMixin, ListView):
    template_name = 'pinboard/account_detail.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    paginator_class = DiggPaginator
    paginate_by = 50
    page_kwarg = 'p'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Account.objects.all())
        return super(AccountDetail, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccountDetail, self).get_context_data(**kwargs)
        context['account'] = self.object
        context['bookmark_list'] = context['object_list']
        return context

    def get_queryset(self):
        return self.object.bookmark_set.all()


class BookmarkDetail(DetailView):
    model = Bookmark

