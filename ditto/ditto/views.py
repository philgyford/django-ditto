import datetime

from django.db import models
from django.http import Http404
from django.utils import timezone
from django.utils.encoding import force_str, force_text
from django.utils.translation import ugettext as _
from django.views.generic import DayArchiveView, DetailView, ListView, TemplateView, View
from django.views.generic.dates import DateMixin, YearMixin, MonthMixin, DayMixin

from .apps import ditto_apps
from .paginator import DiggPaginator


if ditto_apps.is_installed('pinboard'):
    from ..pinboard.models import Bookmark

if ditto_apps.is_installed('twitter'):
    from ..twitter.models import Tweet, User as TwitterUser


class PaginatedListView(ListView):
    """Use this instead of ListView to provide standardised pagination."""
    paginator_class = DiggPaginator
    paginate_by = 50
    page_kwarg = 'p'

    def __init__(self, **kwargs):
        return super().__init__(**kwargs)


class DittoQuerysetsMixin:
    """Contains methods for getting querysets for all the enabled Ditto apps.
    """

    def get_queryset_names(self):
        """A list of all the queryset names for DittoItem-inheriting objects
        for all enabled Ditto apps.
        The order is reasonably important - the first in the returned list will
        be used as the primary queryset in some views.
        """
        names = []

        for app_name in ditto_apps.enabled():
            if app_name == 'pinboard':
                names.append('pinboard_bookmark_list')
            elif app_name == 'twitter':
                names.append('twitter_tweet_list')
                names.append('twitter_favorite_list')

        return names

    def get_first_queryset_name(self):
        return self.get_queryset_names()[0]

    def get_app_querysets(self):
        """Returns a dict of querysets for all the DittoItem-inheriting objects
        for all enabled Ditto apps.
        """
        querysets = {}

        for app_name in ditto_apps.enabled():
            if app_name == 'pinboard':
                querysets['pinboard_bookmark_list'] = Bookmark.public_objects.all()
            elif app_name == 'twitter':
                twitter_users = TwitterUser.objects_with_accounts.all()
                querysets['twitter_tweet_list'] = Tweet.public_objects.filter(user=twitter_users).select_related()
                querysets['twitter_favorite_list'] = Tweet.public_favorite_objects.all().select_related()

        return querysets

    def get_first_queryset(self):
        qs_name = self.get_first_queryset_name()
        return self.get_app_querysets()[qs_name]

    def get_other_querysets(self):
        querysets = self.get_app_querysets()
        del querysets[ self.get_first_queryset_name() ]
        return querysets


class Home(DittoQuerysetsMixin, TemplateView):
    template_name = 'ditto/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        for qs_name, qs in self.get_app_querysets().items():
            context[qs_name] = qs[:5]

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
        if ditto_apps.is_enabled('pinboard'):
            context['pinboard_bookmark_list'] = Bookmark.public_objects.filter(
                                            tags__slug__in=[kwargs['slug']])
        return context


class DayArchive(DittoQuerysetsMixin, DateMixin, YearMixin, MonthMixin, DayMixin, TemplateView):
    """Display all items from a single day, across multiple apps.

    More complicated than I'd like, mainly because we're avoiding using
    BaseDateListView/BaseDayArchiveView/DayArchiveView which assume you have a
    single self.queryset, which we don't. Working around that proved even
    more complicated than this.
    """
    template_name = 'ditto/archive_day.html'
    month_format = '%m'

    # All DittoItem-inheriting classes have 'post_time':
    date_field = 'post_time'

    # Things will break if allow_empty=False, because _get_next_prev() in
    # django.views.generic.dates will then try and check the queryset for
    # objects... we don't have a single queryset.
    allow_empty = True

    allow_future = False

    def get(self, request, *args, **kwargs):
        "404 if allow_future is False and this page is in the future."
        date = self._get_date()

        if not self.get_allow_future() and date > datetime.date.today():
            raise Http404(_(
                "Future items not available because "
                "%(class_name)s.allow_future is False.") % {
                'class_name': self.__class__.__name__,
                },
            )

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Get all the items for today for enabled Ditto apps, add to context.
        Also add a `total_count` parameter.
        """
        context = super().get_context_data(**kwargs)

        date_field = self.get_date_field()
        date = self._get_date()
        total_count = 0

        for qs_name, qs in self.get_app_querysets().items():
            lookup_kwargs = self._make_single_date_lookup(date)
            dated_qs = self.get_dated_queryset(qs, **lookup_kwargs)
            total_count += len(dated_qs)
            context[qs_name] = dated_qs

        context.update(self.get_dated_items())
        context['total_count'] = total_count
        return context

    def get_dated_items(self):
        """
        Return (date_list, items, extra_context) for this request.

        Originally based on the method in BaseDayArchiveView().
        """
        date = self._get_date()

        return self._get_dated_items(date)

    def get_dated_queryset(self, qs, **lookup):
        """
        Get a queryset properly filtered according to `allow_future` and any
        extra lookup kwargs.

        Based on the method in BaseDateListView.
        """
        qs = qs.filter(**lookup)
        date_field = self.get_date_field()
        allow_future = self.get_allow_future()

        if not allow_future:
            now = timezone.now() if self.uses_datetime_field else timezone_today()
            qs = qs.filter(**{'%s__lte' % date_field: now})

        return qs

    def uses_datetime_field(self):
        "Overriding the method in DateMixin."
        return True

    def _get_date(self):
        "Abstracted from BaseDayArchiveView.get_dated_items()."
        year = self.get_year()
        month = self.get_month()
        day = self.get_day()

        date = _date_from_string(year, self.get_year_format(),
                                 month, self.get_month_format(),
                                 day, self.get_day_format())
        return date

    def _get_dated_items(self, date):
        """
        Do the actual heavy lifting of getting the dated items; this accepts a
        date object so that TodayArchiveView can be trivial.

        Based on the method in BaseDayArchiveView().
        """
        return {
            'day': date,
            'previous_day': self.get_previous_day(date),
            'next_day': self.get_next_day(date),
            'previous_month': self.get_previous_month(date),
            'next_month': self.get_next_month(date)
        }

    def get_allow_empty(self):
        """
        Returns ``True`` if the view should display empty lists, and ``False``
        if a 404 should be raised instead.

        From MultipleObjectMixin()
        """
        return self.allow_empty


def _date_from_string(year, year_format, month, month_format, day='', day_format='', delim='__'):
    """
    Helper: get a datetime.date object given a format string and a year,
    month, and possibly day; raise a 404 for an invalid date.

    From django.views.generic.dates
    """
    format = delim.join((year_format, month_format, day_format))
    datestr = delim.join((year, month, day))
    try:
        return datetime.datetime.strptime(force_str(datestr), format).date()
    except ValueError:
        raise Http404(_(u"Invalid date string '%(datestr)s' given format '%(format)s'") % {
            'datestr': datestr,
            'format': format,
        })


