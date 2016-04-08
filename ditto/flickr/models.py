# coding: utf-8
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


class Photo(DittoItemModel):

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
    )

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
        (4, 'Y-m'),
        (6, 'Y'),
        (8, 'Circa...'),
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

    # From https://www.flickr.com/services/api/misc.urls.html
    # Before 2010-05-25 large photos only exist for very large original images.
    # Medium 800, large 1600, and large 2048 photos only exist after 2012-03-01.
    SIZES = {
        'Small square':    's',  # 75x75
        'Large square':    'q',  # 150x150
        'Thumbnail':       't',  # 100
        'Small':           'm',  # 240
        'Small 320':       'n',
        'Medium':          '',   # 500
        'Medium 640':      'z',
        'Medium 800':      'c',
        'Large':           'b',  # 1024
        'Large 1600':      'h',
        'Large 2048':      'k',
        'Original':        'o',
    }

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

    width_t = models.PositiveSmallIntegerField("Thumbnail width",
                                                        null=True, blank=True)
    height_t = models.PositiveSmallIntegerField("Thumbnail height",
                                                        null=True, blank=True)
    width_m = models.PositiveSmallIntegerField("Small width",
                                                        null=True, blank=True)
    height_m = models.PositiveSmallIntegerField("Small height",
                                                        null=True, blank=True)
    width_n = models.PositiveSmallIntegerField("Small 320 width",
                                                        null=True, blank=True)
    height_n = models.PositiveSmallIntegerField("Small 320 height",
                                                        null=True, blank=True)
    width = models.PositiveSmallIntegerField("Medium width",
                                                        null=True, blank=True)
    height = models.PositiveSmallIntegerField("Medium height",
                                                        null=True, blank=True)
    width_z = models.PositiveSmallIntegerField("Medium 640 width",
                                                        null=True, blank=True)
    height_z = models.PositiveSmallIntegerField("Medium 640 height",
                                                        null=True, blank=True)
    width_c = models.PositiveSmallIntegerField("Medium 800 width",
                                                        null=True, blank=True)
    height_c = models.PositiveSmallIntegerField("Medium 800 height",
                                                        null=True, blank=True)
    width_b = models.PositiveSmallIntegerField("Large width",
                                                        null=True, blank=True)
    height_b = models.PositiveSmallIntegerField("Large height",
                                                        null=True, blank=True)
    width_h = models.PositiveSmallIntegerField("Large 1600 width",
                                                        null=True, blank=True)
    height_h = models.PositiveSmallIntegerField("Large 1600 height",
                                                        null=True, blank=True)
    width_k = models.PositiveSmallIntegerField("Large 2048 width",
                                                        null=True, blank=True)
    height_k = models.PositiveSmallIntegerField("Large 2048 height",
                                                        null=True, blank=True)
    width_o = models.PositiveSmallIntegerField("Original width",
                                                        null=True, blank=True)
    height_o = models.PositiveSmallIntegerField("Original height",
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

    tags = TaggableManager(blank=True, through=TaggedPhoto)

    class Meta:
        ordering = ('-taken_time',)

    def summary_source(self):
        """Make the summary that's created when the Photo is saved."""
        return truncate_string(self.description,
                strip_html=True, chars=255, truncate='…', at_word_boundary=True)

    def get_size_variables(self, label):
        """Get the names of the width and height variables for a specific
        photo size.
        label -- The name of a size, eg 'Small square' or 'Large'.
        Returns a list of 0 or 2 variable names, width first.
        eg, ['width_s', 'height_s']
        """
        variables = []
        if label in self.SIZES:
            letter = self.SIZES[label]
            if letter:
                variables = ['width_'+letter, 'height_'+letter]
            else:
                # Medium size.
                variables = ['width', 'height']
        return variables

    @property
    def thumbnail_url(self):
        return self.image_url('t')

    @property
    def small_url(self):
        return self.image_url('m')

    @property
    def small_320_url(self):
        return self.image_url('n')

    @property
    def medium_url(self):
        return self.image_url('-')

    @property
    def medium_640_url(self):
        return self.image_url('z')

    @property
    def medium_800_url(self):
        return self.image_url('c')

    @property
    def large_url(self):
        return self.image_url('b')

    @property
    def large_1600_url(self):
        return self.image_url('h')

    @property
    def large_2048_url(self):
        return self.image_url('k')

    @property
    def original_url(self):
        return 'https://farm%s.static.flickr.com/%s/%s_%s_o.%s' % (
                self.farm, self.server, self.flickr_id, self.original_secret,
                self.original_format)

    def image_url(self, size):
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
    iconserver = models.CharField(null=False, blank=False, max_length=20)
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
        help_text="The time the data was last fetched, and was new or changed.")
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

