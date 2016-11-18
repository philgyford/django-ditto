from django.http import Http404
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin

from taggit.models import Tag

from ..core.views import PaginatedListView
from .models import Account, Photo, Photoset, TaggedPhoto, User


class PhotosOrderMixin(object):
    """
    For pages which list Photos and can change the order they're viewed in.
    Can have 'order' in the GET string, with values of 'uploaded' or 'taken'.

    Adds an 'order' key to the context_data, with value of 'uploaded'/'taken'.
    """

    def get_ordering(self):
        args = self.request.GET
        if 'order' in args and args['order'] == 'taken':
            return '-taken_time'
        else:
            return '-post_time'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = 'uploaded' if self.get_ordering() == '-post_time' else 'taken'
        return context

    def get_queryset(self):
        """Order by -taken_time or -post_time.
        If ordering by taken_time, exclude Photos where taken_unknown = True.
        """
        queryset = super().get_queryset()

        # Not sure why we need to repeat some of this from
        # ListView.get_queryset() here, but the UserDetail page, for one,
        # wasn't ordering by taken_time without this.
        ordering = self.get_ordering()
        if ordering:

            if ordering == '-taken_time':
                # Exclude where we don't know the taken time.
                queryset = queryset.filter(taken_unknown=False)

            import six
            if isinstance(ordering, six.string_types):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset


class HomeView(PhotosOrderMixin, PaginatedListView):
    template_name = 'flickr/home.html'
    paginate_by = 48
    queryset = Photo.public_photo_objects

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account_list'] = Account.objects.all()
        return context

    def get_queryset(self):
        """
        Adding the prefetch_related() to self.queryset caused some tests to
        fail for some reason.
        """
        queryset = super().get_queryset()
        return queryset.prefetch_related('user')



class PhotosetListView(ListView):
    template_name = 'flickr/photoset_list.html'
    queryset = Photoset.objects.all().prefetch_related('primary_photo', 'user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photoset_list'] = context['object_list']
        context['account_list'] = Account.objects.all()
        return context


class SingleUserMixin(SingleObjectMixin):
    """Used for views that need data about a User based on nsid in
    the URL, and its Account if it has one.
    """
    slug_field = 'nsid'
    slug_url_kwarg = 'nsid'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=User.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['flickr_user'] = self.object
        try:
            context['account'] = Account.objects.get(user=self.object)
        except Account.DoesNotExist:
            context['account'] = None
        return context


class UserDetailView(PhotosOrderMixin, SingleUserMixin, PaginatedListView):
    """A single Flickr User and its Photos.
    The user might have an Account associated with it, or might not.
    """
    template_name = 'flickr/user_detail.html'
    paginate_by = 48
    queryset = Photo.public_objects

    def get_queryset(self):
        "All public Photos from this Account."
        queryset = super().get_queryset()
        return queryset.filter(user=self.object).prefetch_related('user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photo_list'] = context['object_list']
        return context


class PhotoDetailView(DetailView):
    """Show a single Photo. It might be posted by one of the Accounts, or might
    be a Photo by someone else, favorited.
    """
    model = Photo
    slug_field = 'flickr_id'
    slug_url_kwarg = 'flickr_id'

    def get_object(self, queryset=None):
        """Do standard DetailView.get_object(), but return 404 if the Photo is
        private, OR if the URL's user NSID doesn't match the photo's."""
        obj = super().get_object(queryset)
        if obj.is_private or obj.user.nsid != self.kwargs['nsid']:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                                      {'verbose_name': obj._meta.verbose_name})
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['flickr_user'] = context['photo'].user
        # We can show favorited Photos; they won't have an associated Account.
        try:
            context['account'] = Account.objects.get(
                                                user=context['flickr_user'])
        except Account.DoesNotExist:
            context['account'] = None
        return context


class TagListView(ListView):
    template_name = 'flickr/tag_list.html'
    context_object_name = 'tag_list'

    def get_queryset(self):
        return Photo.tags.most_common()[:100]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account_list'] = Account.objects.all()
        return context


class TagDetailView(PhotosOrderMixin, SingleObjectMixin, PaginatedListView):
    "All Photos with a certain tag from all Accounts"
    template_name = 'flickr/tag_detail.html'
    allow_empty = False
    queryset = Photo.public_objects.prefetch_related('user')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Tag.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.object
        context['account_list'] = Account.objects.all()
        context['photo_list'] = context['object_list']
        return context

    def get_queryset(self):
        """Show all the public Photos associated with this tag."""
        queryset = super().get_queryset()
        return queryset.filter(tags__slug__in=[self.object.slug])


class UserTagDetailView(PhotosOrderMixin, SingleUserMixin, PaginatedListView):
    "All Photos with a certain Tag from one User"
    template_name = 'flickr/user_tag_detail.html'
    allow_empty = False
    queryset = Photo.public_objects.prefetch_related('user')

    def get(self, request, *args, **kwargs):
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
        context['tag'] = self.tag_object
        context['photo_list'] = context['object_list']
        return context

    def get_queryset(self):
        """Show all the public Photos associated with this user."""
        queryset = super().get_queryset()
        return queryset.filter(user=self.object,
                                    tags__slug__in=[self.kwargs['tag_slug']])


class UserPhotosetListView(SingleUserMixin, ListView):
    template_name = 'flickr/user_photoset_list.html'
    queryset = Photoset.objects.all().prefetch_related('primary_photo', 'user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photoset_list'] = context['object_list']
        return context

    def get_queryset(self):
        """Show all Photosets associated with this user."""
        queryset = super().get_queryset()
        return queryset.filter(user=self.object)


class PhotosetDetailView(PhotosOrderMixin, SingleUserMixin, PaginatedListView):
    template_name = 'flickr/photoset_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # NOTE: photoset.objects.all() will return PRIVATE photos too.
        # You probably don't want to do that.
        context['photoset'] = self.photoset_object
        context['photo_list'] = context['object_list']
        return context

    def get_queryset(self):
        """Show all the public Photos in this Photoset."""
        self.photoset_object = self.get_photoset_object()
        return self.photoset_object.public_photos()

    def get_photoset_object(self):
        """Custom method for fetching the Photoset."""
        try:
            obj = Photoset.objects.get(user=self.object,
                                        flickr_id=self.kwargs['flickr_id'])
        except Photoset.DoesNotExist:
            raise Http404(_("No Photosets found matching the query"))
        return obj

