# coding: utf-8
from django.db import models

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from . import managers
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
    
    # post_time is in DittoItemModel
    last_update_time = models.DateTimeField(null=True, blank=True,
        help_text="The last time the photo, or any of its metadata (tags, comments, etc.) was modified on Flickr. UTC.")
    taken_time = models.DateTimeField(null=True, blank=True,
                                        help_text="In Flickr user's timezone.")
    taken_granularity = models.PositiveSmallIntegerField(
                default=DATE_GRANULARITIES[0][0], choices=DATE_GRANULARITIES)
    taken_unknown = models.BooleanField(default=False)

    view_count = models.PositiveIntegerField(default=0,
                help_text="How many times this had been viewed when fetched")
    comment_count = models.PositiveIntegerField(default=0,
                    help_text="How many comments this had been when fetched")

    photopage_url = models.URLField()

    media = models.CharField(default=MEDIA_TYPES[0][0], choices=MEDIA_TYPES,
                                                                max_length=10)

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
    exif_lens_model = models.CharField(blank=True, max_length=50)
    exif_aperture = models.CharField(blank=True, max_length=30)
    exif_exposure = models.CharField(blank=True, max_length=30)
    exif_flash = models.CharField(blank=True, max_length=30)
    exif_focal_length = models.CharField(blank=True, max_length=10)
    exif_iso = models.IntegerField(blank=True)

    # TODO: NOTES
    # TODO: PEOPLE

    tags = TaggableManager(blank=True, through=TaggedPhoto)

    class Meta:
        ordering = ('-taken_time',)


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

