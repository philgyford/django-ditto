from collections import OrderedDict
import datetime

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import models
from django.http import Http404
from django.shortcuts import redirect
from django.utils import six, timezone
from django.utils.encoding import force_str, force_text
from django.utils.translation import ugettext as _
from django.views.generic import DayArchiveView, DetailView, ListView, TemplateView, View

from .apps import ditto_apps
from .paginator import DiggPaginator

if ditto_apps.is_installed('flickr'):
    from ..flickr.models import Photo

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


class DittoAppsMixin:
    """Contains methods for getting querysets for all the enabled Ditto apps.

    Contains a structure about all the apps and their 'varieties' (eg,
    'tweets' or 'favorites').

    Provides for 'pages' that will show one app+variety per page, based on a
    URL with app_slug and variety_slug keywords.

    NOTE: we have both *_name and *_slug to allow for us to change URLs. Which
    is the case, for example, with using /twitter/likes/ which has a
    variety_name of 'favorite' (rather than 'likes').
    """
    
    # These all set in set_app_and_variety():
    app_name = None  # eg, 'flickr', or 'twitter'.
    app_slug = None  # eg, 'flickr', or 'twitter'.
    variety_name = None  # eg, 'tweet' or 'favorite'.
    variety_slug = None  # eg, 'tweets' or 'likes'.

    # Set in __init__():
    apps = None


    def __init__(self, *args, **kwargs):

        self.apps = []

        enabled_apps = ditto_apps.enabled()

        # The order is important - the first app, and its first variety,
        # will be the defaults.

        if 'flickr' in enabled_apps:
            self.apps.append({
                'slug': 'flickr',
                'name': 'flickr',
                'varieties': [
                    {
                        'slug': 'photos',
                        'name': 'photo',
                        'context_object_name': 'flickr_photo_list',
                        'queryset': Photo.public_objects.all(),
                    },
                ],
            })

        if 'pinboard' in enabled_apps:
            self.apps.append({
                'slug': 'pinboard',
                'name': 'pinboard',
                'varieties': [
                    {
                        'slug': 'bookmarks',
                        'name': 'bookmark',
                        'context_object_name': 'pinboard_bookmark_list',
                        'queryset': Bookmark.public_objects.all(),
                    },
                ],
            })

        if 'twitter' in enabled_apps:
            self.apps.append({
                'slug': 'twitter',
                'name': 'twitter',
                'varieties': [
                    {
                        'slug': 'tweets',
                        'name': 'tweet',
                        'context_object_name': 'twitter_tweet_list',
                        'queryset': Tweet.public_tweet_objects.all().select_related(),
                    },
                    {
                        'slug': 'likes',
                        'name': 'favorite',
                        'context_object_name': 'twitter_favorite_list',
                        'queryset': Tweet.public_favorite_objects.all().select_related(),
                    },
                ],
            })

        super().__init__(*args, **kwargs)

    def set_app_and_variety(self, **kwargs):
        """
        MUST be called by childs' get() methods, before they do much else.
        I don't like this reliance, but not sure how else to set app_name and
        variety_name before doing other get() stuff.

        Child get() methods should handle what happens if one or both of
        self.app_name and self.variety_name are left as None after this.

        Based on URL kwargs, sets the values of:
            * self.app_name
            * self.app_slug
            * self.variety_name
            * self.variety_slug
        So long as the 'app' and 'variety' slugs are valid.
        """
        app_slug = kwargs.get('app', None)
        variety_slug = kwargs.get('variety', None)

        if self.is_valid_app_slug(app_slug):
            self.app_name = self.get_app_name_from_slug(app_slug)

            if self.is_valid_variety_slug(app_slug, variety_slug):
                self.variety_name = self.get_variety_name_from_slugs(
                                                        app_slug, variety_slug)
            elif variety_slug:
                raise Http404(
                    "'%s' is not a valid variety slug for the '%s' app slug."%\
                                                    (variety_slug, app_slug))
        elif app_slug:
            raise Http404("'%s' is not a valid app slug."% app_slug)

        self.app_slug = app_slug
        self.variety_slug = variety_slug

    def get_context_object_name(self, object_list):
        """
        Get the name of the item to be used in the context.
        eg, 'twitter_favorite_list'.

        Overriding MultipleObjectMixin.get_context_object_name()
        """
        return self.get_context_object_name_for_app_variety(
                                            self.app_name, self.variety_name)

    def get_queryset(self):
        queryset = self.get_queryset_for_app_variety(
                                            self.app_name, self.variety_name)

        if queryset is None:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. "
                "%(cls)s.get_queryset() can't find the correct "
                "queryset for this app and variety."% {
                    'cls': self.__class__.__name__
                }
            )

        return queryset

    def get_context_data(self, **kwargs):
        """Add context stuff related to apps, varieties, etc."""
        context = super().get_context_data(**kwargs)
        context['ditto_app_name'] = self.app_name
        context['ditto_app_slug'] = self.app_slug
        context['ditto_variety_name'] = self.variety_name
        context['ditto_variety_slug'] = self.variety_slug
        return context

    # Below -- convenience methods for getting bits of data from the self.apps
    # structure.

    def get_app_varieties(self):
        """A list of tuples mapping app_name to each variety_name.
        May have duplicate app_names if the app has more than one variety."""
        app_varieties = []
        for app in self.apps:
            for variety in app['varieties']:
                app_varieties.append( (app['name'], variety['name']) )
        return app_varieties

    def get_app_slugs(self):
        """eg ['flickr', 'pinboard', 'twitter']."""
        return [app['slug'] for app in self.apps]

    def get_variety_slugs(self, app_slug):
        "A list of the slugs for the varieties of the app indicated by app_slug"
        app = self.get_app_from_slug(app_slug)
        return [ variety['slug'] for variety in app['varieties'] ]

    def is_valid_app_slug(self, app_slug):
        "Does this app slug exist in self.apps?"
        return (app_slug in self.get_app_slugs())

    def is_valid_variety_slug(self, app_slug, variety_slug):
        "Does this variety slug exist for app_slug's app in self.apps?"
        return (variety_slug in self.get_variety_slugs(app_slug))

    def get_default_app_slug(self):
        "Just the slug of the first app in the list."
        return self.apps[0]['slug']

    def get_default_variety_slug(self):
        "Just the slug of the first variety of the first app in the list."
        return self.apps[0]['varieties'][0]['slug']

    def get_default_variety_slug_for_app_slug(self, app_slug):
        "The slug of the first variety for the app indicated by app_slug."
        return self.get_app_from_slug(app_slug)['varieties'][0]['slug']

    def get_app_name_from_slug(self, app_slug):
        "What's the name of the app that has the slug app_slug?"
        return self.get_app_from_slug(app_slug)['name']

    def get_variety_name_from_slugs(self, app_slug, variety_slug):
        """What's the name of the variety that has the slug variety_slug, in
        the app that has the slug app_slug?"""
        variety = self.get_variety_from_slugs(app_slug, variety_slug)
        return variety['name']

    def get_app_from_slug(self, app_slug):
        "Get all the data in self.apps for the app with the slug app_slug"
        return list(filter(lambda a: a['slug'] == app_slug, self.apps))[0]

    def get_variety_from_slugs(self, app_slug, variety_slug):
        """Given app_slug and variety_slug, return the data in self.apps for
        that variety."""
        app = self.get_app_from_slug(app_slug)
        varieties = app['varieties']
        return list(filter(lambda v: v['slug'] == variety_slug, varieties))[0]

    def get_app_from_name(self, app_name):
        "Get all the data in self.apps for the app with the name app_name"
        return list(filter(lambda a: a['name'] == app_name, self.apps))[0]

    def get_variety_from_names(self, app_name, variety_name):
        """Given app_name and variety_name, return the data in self.apps for
        that variety."""
        app = self.get_app_from_name(app_name)
        varieties = app['varieties']
        return list(filter(lambda v: v['name'] == variety_name, varieties))[0]

    def get_app_slug_from_name(self, app_name):
        return self.get_app_from_name(app_name)['slug']

    def get_variety_slug_from_names(self, app_name, variety_name):
        return self.get_variety_from_names(app_name, variety_name)['slug']

    def get_context_object_name_for_app_variety(self, app_name, variety_name):
        """Given app_name and variety_name, return the context_object_name in
        self.apps for that variety."""
        variety = self.get_variety_from_names(app_name, variety_name)
        return variety['context_object_name']

    def get_queryset_for_app_variety(self, app_name, variety_name):
        """Given app_name and variety_name, return the queryset in
        self.apps for that variety."""
        variety = self.get_variety_from_names(app_name, variety_name)
        return variety['queryset']


class Home(DittoAppsMixin, TemplateView):
    template_name = 'ditto/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        for app_name, variety_name in self.get_app_varieties():
            queryset = self.get_queryset_for_app_variety(app_name, variety_name)
            context_object_name = self.get_context_object_name_for_app_variety(
                                                        app_name, variety_name)

            if context_object_name == 'flickr_photo_list':
                context[context_object_name] = queryset[:4]
            else:
                context[context_object_name] = queryset[:3]

        return context


class DayArchive(DittoAppsMixin, DayArchiveView):
    """A single app+variety for a single day.
    eg /2016/04/20/twitter/likes
    """
    template_name = 'ditto/archive_day.html'
    month_format = '%m'
    allow_empty = True
    allow_future = False

    # All DittoItem-inheriting classes have 'post_time':
    date_field = 'post_time'

    def get(self, request, *args, **kwargs):
        """Sets up self.app_name etc, and handles redirects to defaults if
        both are missing, or if app_name is valid but has no variety.
        """

        self.set_app_and_variety(**kwargs)

        if self.variety_name is None:
            if self.app_name is None:
                # Redirect to default app and variety for this date.
                return redirect(
                    reverse('ditto:day_archive', kwargs={
                        'year':     self.get_year(),
                        'month':    self.get_month(),
                        'day':      self.get_day(),
                        'app':      self.get_default_app_slug(),
                        'variety':  self.get_default_variety_slug(),
                }) )
            else:
                # Redirect to the default variety for this app.
                return redirect(
                    reverse('ditto:day_archive', kwargs={
                        'year': self.get_year(),
                        'month': self.get_month(),
                        'day': self.get_day(),
                        'app': self.app_slug,
                        'variety': self.get_default_variety_slug_for_app_slug(
                                                                self.app_slug),
                }) )

        return super().get(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_counts'] = self.get_all_counts()
        return context

    def get_all_counts(self):
        """
        For all of the querysets for all enabled apps, get the count of items
        they have for this day.

        Returns an OrderedDict like:
            [ ('twitter_tweet_list', 6), (...), ]

        Most of this is adapted from standard DayArchiveView methods, so that
        we can run it against each queryset in turn, rather than only
        self.queryset.
        """

        # From get_dated_items():
        year = self.get_year()
        month = self.get_month()
        day = self.get_day()
        date = _date_from_string(year, self.get_year_format(),
                                 month, self.get_month_format(),
                                 day, self.get_day_format())

        # From _get_dated_items():
        lookup_kwargs = self._make_single_date_lookup(date)

        # Adapted from get_dated_queryset():

        date_field = self.get_date_field()
        allow_future = self.get_allow_future()
        allow_empty = self.get_allow_empty()

        # Want to keep them in the same order as get_queryset_names() provides.
        counts = []

        for app_name, variety_name in self.get_app_varieties():
            qs = self.get_queryset_for_app_variety(app_name, variety_name)
            qs = qs.filter(**lookup_kwargs)
            paginate_by = self.get_paginate_by(qs)
            if not allow_future:
                now = timezone.now() if self.uses_datetime_field else timezone_today()
                qs = qs.filter(**{'%s__lte' % date_field: now})
            if not allow_empty:
                # When pagination is enabled, it's better to do a cheap query
                # than to load the unpaginated queryset in memory.
                is_empty = len(qs) == 0 if paginate_by is None else not qs.exists()
                if is_empty:
                    raise Http404(_("No %(verbose_name_plural)s available") % {
                        'verbose_name_plural': force_text(qs.model._meta.verbose_name_plural)
                    })
            counts.append({
                'count':        qs.count(),
                'app_name':     app_name,
                'variety_name': variety_name,
                'app_slug':     self.get_app_slug_from_name(app_name),
                'variety_slug': self.get_variety_slug_from_names(
                                                    app_name, variety_name),
            })

        return counts


#class TagList(TemplateView):
    #"Doesn't really do anything at the moment."
    #template_name = 'ditto/tag_list.html'


#class TagDetail(TemplateView):
    #"All items with a certain tag"
    #template_name = 'ditto/tag_detail.html'

    #def get_context_data(self, **kwargs):
        #context = super().get_context_data(**kwargs)
        #context['tag'] = kwargs['slug']
        #if ditto_apps.is_enabled('pinboard'):
            #context['pinboard_bookmark_list'] = Bookmark.public_objects.filter(
                                            #tags__slug__in=[kwargs['slug']])
        #return context


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


