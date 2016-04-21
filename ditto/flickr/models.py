# coding: utf-8
from django.core.urlresolvers import reverse
from django.db import models

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from . import managers
from ..ditto.utils import truncate_string
from ..ditto.models import DiffModelMixin, DittoItemModel, TimeStampedModelMixin


class Account(TimeStampedModelMixin, models.Model):
    user = models.ForeignKey('User', blank=True, null=True,
                                                    on_delete=models.SET_NULL)

    api_key = models.CharField(blank=True, max_length=255,
                                                        verbose_name='API Key')
    api_secret = models.CharField(blank=True, max_length=255,
                                                    verbose_name='API Secret')

    is_active = models.BooleanField(default=True,
                            help_text="If false, new Photos won't be fetched.")

    def __str__(self):
        if self.user:
            return str(self.user)
        else:
            return '%d' % self.pk

    class Meta:
        ordering = ['user__realname']

    def get_absolute_url(self):
        if self.user:
            return reverse('flickr:user_detail',
                        kwargs={'nsid': self.user.nsid})
        else:
            return ''

    def has_credentials(self):
        "Does this at least have something in its API fields? True or False"
        if self.api_key and self.api_secret:
            return True
        else:
            return False


class TaggedPhoto(TaggedItemBase):
    """
    Describes the relationship between a django-taggit Tag and a Photo.
    Flickr has various fields which are unique to this relationship, rather
    than the Tag itself.

    Get the TaggedPhoto objects for one tag object:
        tagged_photo = TaggedPhoto.objects.filter(tag_id=tag)

    Get the TaggedPhoto objects for a particular photo object:
        tagged_photo = TaggedPhoto.objects.filter(content_object=photo)

    Access the Tag info for a TaggedPhoto, eg:
        tagged_photo.tag.slug
    """
    flickr_id = models.CharField(max_length=200, verbose_name="Flickr ID",
                                            help_text="The tag's ID on Flickr")
    author = models.ForeignKey('User')
    machine_tag = models.BooleanField(default=False)
    content_object = models.ForeignKey('Photo',
                                related_name="%(app_label)s_%(class)s_items")

    class Meta:
        verbose_name = 'Photo/Tag Relationship'


class ExtraPhotoManagers(models.Model):
    """Managers to use in the Photo model, in addition to the defaults defined
    in DittoItemModel.
    These need to be here, rather than in the Photo model, or they will
    override those in DittoItemModel.
    """
    photo_objects = managers.PhotosManager()
    public_photo_objects = managers.PublicPhotosManager()

    class Meta:
        abstract = True


class Photo(DittoItemModel, ExtraPhotoManagers):

    # From
    # https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.html
    LICENSES = (
        ('0', 'All Rights Reserved'),
        ('1', 'Attribution-NonCommercial-ShareAlike License'),
        ('2', 'Attribution-NonCommercial License'),
        ('3', 'Attribution-NonCommercial-NoDerivs License'),
        ('4', 'Attribution License'),
        ('5', 'Attribution-ShareAlike License'),
        ('6', 'Attribution-NoDerivs License'),
        ('7', 'No known copyright restrictions'),
        ('8', 'United States Government Work'),
        ('9', 'Public Domain Dedication (CC0)'),
        ('10', 'Public Domain Mark'),
        # Adding these so we'll at least have options for any future licenses:
        ('11', 'Unused'),
        ('12', 'Unused'),
        ('13', 'Unused'),
        ('14', 'Unused'),
        ('15', 'Unused'),
        ('16', 'Unused'),
        ('17', 'Unused'),
        ('18', 'Unused'),
        ('19', 'Unused'),
        ('20', 'Unused'),
    )

    # Used in ditto/flickr/templatetags/flickr.py
    LICENSE_URLS = {
        '0': '',
        '1': 'https://creativecommons.org/licenses/by-nc-sa/2.0/',
        '2': 'https://creativecommons.org/licenses/by-nc/2.0/',
        '3': 'https://creativecommons.org/licenses/by-nc-nd/2.0/',
        '4': 'https://creativecommons.org/licenses/by/2.0/',
        '5': 'https://creativecommons.org/licenses/by-sa/2.0/',
        '6': 'https://creativecommons.org/licenses/by-nd/2.0/',
        '7': 'https://www.flickr.com/commons/usage/',
        '8': 'http://www.usa.gov/copyright.shtml',
        '9': 'https://creativecommons.org/publicdomain/zero/1.0/',
        '10': 'https://creativecommons.org/publicdomain/mark/1.0/',
    }

    # https://www.flickr.com/services/api/flickr.photos.setSafetyLevel.html
    SAFETY_LEVELS = (
        (0, 'none'), # Some have 0 as a safety_level.
        (1, 'Safe'),
        (2, 'Moderate'),
        (3, 'Restricted'),
    )

    # From https://www.flickr.com/services/api/misc.dates.html
    DATE_GRANULARITIES = (
        (0, 'Y-m-d H:i:s'),
        (1, 'Unused'),
        (2, 'Unused'),
        (3, 'Unused'),
        (4, 'Y-m'),
        (5, 'Unused'),
        (6, 'Y'),
        (7, 'Unused'),
        (8, 'Circa...'),
        (9, 'Unused'),
        (10, 'Unused'),
    )

    MEDIA_TYPES = (
        ('photo', 'Photo'),
        ('video', 'Video'),
    )

    # From https://www.flickr.com/services/api/flickr.photos.search.html
    LOCATION_CONTEXTS = (
        (0, 'not defined'),
        (1, 'indoors'),
        (2, 'outdoors'),
    )

    user = models.ForeignKey('User')

    flickr_id = models.BigIntegerField(unique=True, db_index=True,
                                    help_text="ID of this photo on Flickr.")
    # title is in DittoItemModel
    # is_private is in DittoItemModel
    description = models.TextField(blank=True, help_text="Can contain HTML")

    secret = models.CharField(max_length=20)
    original_secret = models.CharField(max_length=20)
    server = models.CharField(max_length=20)
    farm = models.PositiveSmallIntegerField()

    license = models.CharField(max_length=50, choices=LICENSES)
    rotation = models.PositiveSmallIntegerField(default=0,
        help_text="Current clockwise rotation, in degrees, by which the smaller image sizes differ from the original image.")
    original_format = models.CharField(max_length=10, help_text="eg, 'png'")
    safety_level = models.PositiveSmallIntegerField(
                            default=SAFETY_LEVELS[0][0], choices=SAFETY_LEVELS)

    has_people = models.BooleanField(default=False,
                            help_text="Are there Flickr users in this photo?")

    # post_time (in GMT) is in DittoItemModel
    last_update_time = models.DateTimeField(null=True, blank=True,
        help_text="The last time the photo, or any of its metadata (tags, comments, etc.) was modified on Flickr. UTC.")
    taken_time = models.DateTimeField(null=True, blank=True,
                                help_text="In the Flickr user's timezone.")
    taken_granularity = models.PositiveSmallIntegerField(
                default=DATE_GRANULARITIES[0][0], choices=DATE_GRANULARITIES)
    taken_unknown = models.BooleanField(default=False)

    view_count = models.PositiveIntegerField(default=0,
                help_text="How many times this had been viewed when fetched")
    comment_count = models.PositiveIntegerField(default=0,
                    help_text="How many comments this had been when fetched")

    media = models.CharField(default=MEDIA_TYPES[0][0], choices=MEDIA_TYPES,
                                                                max_length=10)

    # SIZES ##################################################################

    sizes_raw = models.TextField(blank=True,
            help_text="eg, the raw JSON from the API - flickr.photos.getSizes.")

    thumbnail_width = models.PositiveSmallIntegerField(null=True, blank=True)
    thumbnail_height = models.PositiveSmallIntegerField(null=True, blank=True)
    small_width = models.PositiveSmallIntegerField(null=True, blank=True)
    small_height = models.PositiveSmallIntegerField(null=True, blank=True)
    small_320_width = models.PositiveSmallIntegerField(null=True, blank=True)
    small_320_height = models.PositiveSmallIntegerField(null=True, blank=True)
    medium_width = models.PositiveSmallIntegerField(null=True, blank=True)
    medium_height = models.PositiveSmallIntegerField(null=True, blank=True)
    medium_640_width = models.PositiveSmallIntegerField(null=True, blank=True)
    medium_640_height = models.PositiveSmallIntegerField(null=True, blank=True)
    medium_800_width = models.PositiveSmallIntegerField(null=True, blank=True)
    medium_800_height = models.PositiveSmallIntegerField(null=True, blank=True)
    large_width = models.PositiveSmallIntegerField(null=True, blank=True)
    large_height = models.PositiveSmallIntegerField(null=True, blank=True)
    large_1600_width = models.PositiveSmallIntegerField(null=True, blank=True)
    large_1600_height = models.PositiveSmallIntegerField(null=True, blank=True)
    large_2048_width = models.PositiveSmallIntegerField(null=True, blank=True)
    large_2048_height = models.PositiveSmallIntegerField(null=True, blank=True)
    original_width = models.PositiveSmallIntegerField(null=True, blank=True)
    original_height = models.PositiveSmallIntegerField(null=True, blank=True)

    # Video sizes; when media='video'.
    mobile_mp4_width = models.PositiveSmallIntegerField("Mobile MP4 width",
                                                        null=True, blank=True)
    mobile_mp4_height = models.PositiveSmallIntegerField("Mobile MP4 height",
                                                        null=True, blank=True)
    site_mp4_width = models.PositiveSmallIntegerField("Site MP4 width",
                                                        null=True, blank=True)
    site_mp4_height = models.PositiveSmallIntegerField("Site MP4 height",
                                                        null=True, blank=True)
    hd_mp4_width = models.PositiveSmallIntegerField("HD MP4 width",
                                                        null=True, blank=True)
    hd_mp4_height = models.PositiveSmallIntegerField("HD MP4 height",
                                                        null=True, blank=True)
    video_original_width = models.PositiveSmallIntegerField(
                                                        null=True, blank=True)
    video_original_height = models.PositiveSmallIntegerField(
                                                        null=True, blank=True)


    # LOCATION ###############################################################

    geo_is_private = models.BooleanField(default=False, null=False, blank=False,
        help_text="If true, the Photo's location info should not be displayed.")

    # latitude and longitude are in DittoItemModel

    # https://www.flickr.com/services/api/flickr.photos.search.html
    location_accuracy = models.PositiveSmallIntegerField(
        null=True, blank=True, default=1,
        help_text="World is 1; Country is ~3; Region is ~6; City is ~11; Street is ~16.")
    # https://www.flickr.com/services/api/flickr.photos.search.html
    location_context = models.PositiveSmallIntegerField(
                    default=LOCATION_CONTEXTS[0][0], choices=LOCATION_CONTEXTS)
    location_place_id = models.CharField(blank=True, max_length=30)
    location_woeid = models.CharField(blank=True, max_length=30)

    locality_name = models.CharField(blank=True, max_length=255)
    locality_place_id = models.CharField(blank=True, max_length=30)
    locality_woeid = models.CharField(blank=True, max_length=30)
    county_name = models.CharField(blank=True, max_length=255)
    county_place_id = models.CharField(blank=True, max_length=30)
    county_woeid = models.CharField(blank=True, max_length=30)
    region_name = models.CharField(blank=True, max_length=255)
    region_place_id = models.CharField(blank=True, max_length=30)
    region_woeid = models.CharField(blank=True, max_length=30)
    country_name = models.CharField(blank=True, max_length=255)
    country_place_id = models.CharField(blank=True, max_length=30)
    country_woeid = models.CharField(blank=True, max_length=30)

    # EXIF ###################################################################

    # EXIF data comes from a separate query, so store its JSON here.
    exif_raw = models.TextField(blank=True,
            help_text="The raw JSON from the API from flickr.photos.getExif.")
    exif_camera = models.CharField(blank=True, max_length=50)
    exif_lens_model = models.CharField(blank=True, max_length=50,
            help_text="eg, 'E PZ 16-50mm F3.5-5.6 OSS'.")
    exif_aperture = models.CharField(blank=True, max_length=30,
            help_text="eg, 'f/13.0'.")
    exif_exposure = models.CharField(blank=True, max_length=30,
            help_text="eg, '0.01 sec (1/100)'.")
    exif_flash = models.CharField(blank=True, max_length=30,
            help_text="eg, 'Off, Did not fire'.")
    exif_focal_length = models.CharField(blank=True, max_length=10,
            help_text="eg, '38 mm.'")
    exif_iso = models.IntegerField(blank=True, null=True, help_text="eg, '100'.")

    # TODO: NOTES
    # TODO: PEOPLE

    tags = TaggableManager(blank=True, manager=managers._PhotoTaggableManager,
                                                        through=TaggedPhoto)

    class Meta:
        ordering = ('-post_time',)

    def summary_source(self):
        """Make the summary that's created when the Photo is saved."""
        return truncate_string(self.description,
                strip_html=True, chars=255, truncate='…', at_word_boundary=True)

    @property
    def account(self):
        "The Account whose photo this is, if any. Otherwise, None."
        try:
            return self.user.account_set.all()[0]
        except IndexError:
            return None

    @property
    def location_str(self):
        "eg 'Abbey Dore, Herefordshire, England, United Kingdom'."
        strs = [
            self.locality_name,
            self.county_name,
            self.region_name,
            self.country_name,
        ]
        return ', '.join(filter(None, strs))

    @property
    def has_exif(self):
        "Do we have any EXIF info to display?"
        props = ['exif_camera', 'exif_lens_model', 'exif_aperture',
                'exif_exposure', 'exif_flash', 'exif_focal_length', 'exif_iso',]
        has_exif = False

        for prop in props:
            if getattr(self, prop):
                has_exif = True
                break

        return has_exif

    @property
    def square_url(self):
        return self._image_url('s')

    @property
    def large_square_url(self):
        return self._image_url('q')

    @property
    def thumbnail_url(self):
        return self._image_url('t')

    @property
    def small_url(self):
        return self._image_url('m')

    @property
    def small_320_url(self):
        return self._image_url('n')

    @property
    def medium_url(self):
        return self._image_url('-')

    @property
    def medium_640_url(self):
        return self._image_url('z')

    @property
    def medium_800_url(self):
        return self._image_url('c')

    @property
    def large_url(self):
        return self._image_url('b')

    @property
    def large_1600_url(self):
        return self._image_url('h')

    @property
    def large_2048_url(self):
        return self._image_url('k')

    @property
    def original_url(self):
        return 'https://farm%s.static.flickr.com/%s/%s_%s_o.%s' % (
                self.farm, self.server, self.flickr_id, self.original_secret,
                self.original_format)

    @property
    def mobile_mp4_url(self):
        return self._video_url('mobile')

    @property
    def site_mp4_url(self):
        return self._video_url('site')

    @property
    def hd_mp4_url(self):
        return self._video_url('hd')

    @property
    def original_video_url(self):
        return self._video_url('orig')

    def _video_url(self, size):
        """Helper for the video URL property methods.
        Returns None for photos, or a URL like
        https://www.flickr.com/photos/philgyford/25743649964/play/site/a8bd5ddf59/
        for videos.
        size -- 'site', 'mobile', 'hd', or 'orig'
        """
        if self.media == 'photo':
            return None
        else:
            return '%splay/%s/%s/' % (self.permalink, size, self.secret)

    def _image_url(self, size):
        "Helper for the photo url property methods."
        size_ext = ''
        if size != '-':
            # All non-Medium-size images:
            size_ext = '_%s' % size
        return 'https://farm%s.static.flickr.com/%s/%s_%s%s.jpg' % (
                self.farm, self.server, self.flickr_id, self.secret, size_ext)


class User(TimeStampedModelMixin, DiffModelMixin, models.Model):
    nsid = models.CharField(null=False, blank=False, unique=True,
                                        max_length=50, verbose_name='NSID')
    is_pro = models.BooleanField(null=False, blank=False, default=False,
                                                    verbose_name='Is Pro?')
    iconserver = models.PositiveIntegerField(null=False, blank=False,
                                                                   default=0)
    iconfarm = models.PositiveIntegerField(null=False, blank=False)

    username = models.CharField(null=False, blank=False, unique=True,
                                                                  max_length=50)
    realname = models.CharField(null=False, blank=False, max_length=255)
    location = models.CharField(null=False, blank=True, max_length=255)
    description = models.TextField(null=False, blank=True,
                                                help_text="May contain HTML")

    photos_url = models.URLField(null=False, blank=False, max_length=255,
                                                    verbose_name='Photos URL')
    profile_url = models.URLField(null=False, blank=False, max_length=255,
                                                    verbose_name='Profile URL')

    photos_count = models.PositiveIntegerField(null=False, blank=False,
                                                                      default=0)
    photos_views = models.PositiveIntegerField(null=False, blank=False,
                                                                      default=0)
    photos_first_date = models.DateTimeField(null=True, blank=False)
    photos_first_date_taken = models.DateTimeField(null=True, blank=False)

    # As on DittoItemModel:
    fetch_time = models.DateTimeField(null=True, blank=True,
                            help_text="The time the data was last fetched.")
    raw = models.TextField(null=False, blank=True,
                                    help_text="eg, the raw JSON from the API.")
    timezone_id = models.CharField(null=False, blank=False, max_length=50,
                                            help_text="eg, 'Europe/London'.")

    objects = models.Manager()
    # All Users that have Accounts:
    objects_with_accounts = managers.WithAccountsManager()

    def __str__(self):
        return self.realname

    class Meta:
        ordering = ['realname']

    @property
    def name(self):
        return self.realname

    @property
    def permalink(self):
        return self.photos_url

    @property
    def icon_url(self):
        if self.iconserver:
            return 'https://farm%s.staticflickr.com/%s/buddyicons/%s.jpg' % \
                                    (self.iconfarm, self.iconserver, self.nsid)
        else:
            return 'https://www.flickr.com/images/buddyicon.gif'