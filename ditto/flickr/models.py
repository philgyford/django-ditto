# coding: utf-8
from django.db import models

try:
    from django.urls import reverse
except ImportError:
    # For Django 1.8
    from django.urls import reverse
from django.templatetags.static import static

from imagekit.cachefiles import ImageCacheFile
from sortedm2m.fields import SortedManyToManyField
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from . import app_settings
from . import imagegenerators
from . import managers
from ..core.models import DiffModelMixin, DittoItemModel, TimeStampedModelMixin


class Account(TimeStampedModelMixin, models.Model):
    user = models.ForeignKey("User", blank=True, null=True, on_delete=models.SET_NULL)

    api_key = models.CharField(blank=True, max_length=255, verbose_name="API Key")
    api_secret = models.CharField(blank=True, max_length=255, verbose_name="API Secret")

    is_active = models.BooleanField(
        default=True, help_text="If false, new Photos won't be fetched."
    )

    def __str__(self):
        if self.user:
            return str(self.user)
        else:
            return "%d" % self.pk

    class Meta:
        ordering = ["user__realname"]

    def get_absolute_url(self):
        if self.user:
            return reverse("flickr:user_detail", kwargs={"nsid": self.user.nsid})
        else:
            return ""

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

    flickr_id = models.CharField(
        max_length=200, verbose_name="Flickr ID", help_text="The tag's ID on Flickr"
    )
    author = models.ForeignKey("User", on_delete=models.CASCADE)
    machine_tag = models.BooleanField(default=False)
    content_object = models.ForeignKey(
        "Photo", on_delete=models.CASCADE, related_name="%(app_label)s_%(class)s_items"
    )

    class Meta:
        verbose_name = "Photo/Tag Relationship"


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

    ditto_item_name = "flickr_photo"

    # The keys in this dict are what we use internally, for method names and
    # for the sizes of PhotoDownloads.
    # The 'label's are used in Flickr's API to identify sizes.
    # The 'generator's are used to create an image of that size from original
    # files.
    # See https://www.flickr.com/services/api/misc.urls.html
    PHOTO_SIZES = {
        "square": {
            "label": "Square",
            "suffix": "s",  # Used in this size's flickr.com URL.
            "generator": imagegenerators.Square,
        },
        "large_square": {
            "label": "Large square",
            "suffix": "q",
            "generator": imagegenerators.LargeSquare,
        },
        "thumbnail": {
            "label": "Thumbnail",
            "suffix": "t",
            "generator": imagegenerators.Thumbnail,
        },
        "small": {"label": "Small", "suffix": "m", "generator": imagegenerators.Small},
        "small_320": {
            "label": "Small 320",
            "suffix": "n",
            "generator": imagegenerators.Small320,
        },
        "medium": {
            "label": "Medium",
            "suffix": "",
            "generator": imagegenerators.Medium,
        },
        "medium_640": {
            "label": "Medium 640",
            "suffix": "z",
            "generator": imagegenerators.Medium640,
        },
        # Only exist after March 1st 2012.
        "medium_800": {
            "label": "Medium 800",
            "suffix": "c",
            "generator": imagegenerators.Medium800,
        },
        # Before May 25th 2010, large only exist for very large original images.
        "large": {"label": "Large", "suffix": "b", "generator": imagegenerators.Large},
        # Introduced March 2012, but since backfilled to older photos
        # https://www.flickr.com/help/forum/en-us/72157710955873986/
        "large_1600": {
            "label": "Large 1600",
            "suffix": "h",
            "generator": imagegenerators.Large1600,
        },
        "large_2048": {
            "label": "Large 2048",
            "suffix": "k",
            "generator": imagegenerators.Large2048,
        },
        # Up to 5K sizes announced October 2018
        # https://blog.flickr.net/en/2018/10/31/putting-your-best-photo-forward-flickr-updates/
        "x_large_3k": {
            "label": "X-Large 3K",
            "suffix": "3k",
            "generator": imagegenerators.XLarge3K,
        },
        "x_large_4k": {
            "label": "X-Large 4K",
            "suffix": "4k",
            "generator": imagegenerators.XLarge4K,
        },
        "x_large_5k": {
            "label": "X-Large 5K",
            "suffix": "5k",
            "generator": imagegenerators.XLarge5K,
        },
        # 6K size announced October 2019
        # https://www.flickr.com/help/forum/en-us/72157711364062311/
        "x_large_6k": {
            "label": "X-Large 6K",
            "suffix": "6k",
            "generator": imagegenerators.XLarge6K,
        },
        "original": {"label": "Original", "suffix": "o"},
    }

    VIDEO_SIZES = {
        "mobile_mp4": {
            "label": "Mobile MP4",
            "url_size": "mobile",  # Used in this size's flickr.com URL.
        },
        "site_mp4": {"label": "Site MP4", "url_size": "site"},
        "hd_mp4": {"label": "HD MP4", "url_size": "hd"},
        "video_original": {"label": "Video Original", "url_size": "orig"},
    }

    # From
    # https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.html
    LICENSES = (
        ("0", "All Rights Reserved"),
        ("1", "Attribution-NonCommercial-ShareAlike License"),
        ("2", "Attribution-NonCommercial License"),
        ("3", "Attribution-NonCommercial-NoDerivs License"),
        ("4", "Attribution License"),
        ("5", "Attribution-ShareAlike License"),
        ("6", "Attribution-NoDerivs License"),
        ("7", "No known copyright restrictions"),
        ("8", "United States Government Work"),
        ("9", "Public Domain Dedication (CC0)"),
        ("10", "Public Domain Mark"),
        # Adding these so we'll at least have options for any future licenses:
        ("11", "Unused"),
        ("12", "Unused"),
        ("13", "Unused"),
        ("14", "Unused"),
        ("15", "Unused"),
        ("16", "Unused"),
        ("17", "Unused"),
        ("18", "Unused"),
        ("19", "Unused"),
        ("20", "Unused"),
    )

    # Used in ditto/flickr/templatetags/flickr.py
    LICENSE_URLS = {
        "0": "",
        "1": "https://creativecommons.org/licenses/by-nc-sa/2.0/",
        "2": "https://creativecommons.org/licenses/by-nc/2.0/",
        "3": "https://creativecommons.org/licenses/by-nc-nd/2.0/",
        "4": "https://creativecommons.org/licenses/by/2.0/",
        "5": "https://creativecommons.org/licenses/by-sa/2.0/",
        "6": "https://creativecommons.org/licenses/by-nd/2.0/",
        "7": "https://www.flickr.com/commons/usage/",
        "8": "http://www.usa.gov/copyright.shtml",
        "9": "https://creativecommons.org/publicdomain/zero/1.0/",
        "10": "https://creativecommons.org/publicdomain/mark/1.0/",
    }

    # https://www.flickr.com/services/api/flickr.photos.setSafetyLevel.html
    SAFETY_LEVELS = (
        (0, "None"),  # Some have 0 as a safety_level.
        (1, "Safe"),
        (2, "Moderate"),
        (3, "Restricted"),
    )

    # From https://www.flickr.com/services/api/misc.dates.html
    DATE_GRANULARITIES = (
        (0, "Y-m-d H:i:s"),
        (1, "Unused"),
        (2, "Unused"),
        (3, "Unused"),
        (4, "Y-m"),
        (5, "Unused"),
        (6, "Y"),
        (7, "Unused"),
        (8, "Circa..."),
        (9, "Unused"),
        (10, "Unused"),
    )

    MEDIA_TYPES = (
        ("photo", "Photo"),
        ("video", "Video"),
    )

    # From https://www.flickr.com/services/api/flickr.photos.search.html
    LOCATION_CONTEXTS = (
        (0, "not defined"),
        (1, "indoors"),
        (2, "outdoors"),
    )

    # Properties inherited from DittoItemModel:
    #
    # title         (CharField)
    # permalink     (URLField)
    # summary       (CharField)
    # is_private    (BooleanField)
    # fetch_time    (DateTimeField, UTC)
    # post_time     (DateTimeField, UTC)
    # latitude      (DecimalField)
    # longitude     (DecimalField)
    # raw           (TextField)

    user = models.ForeignKey("User", on_delete=models.CASCADE)

    flickr_id = models.BigIntegerField(
        unique=True, db_index=True, help_text="ID of this photo on Flickr."
    )
    description = models.TextField(blank=True, help_text="Can contain HTML")

    secret = models.CharField(max_length=20)
    original_secret = models.CharField(max_length=20)
    server = models.CharField(max_length=20)
    farm = models.PositiveSmallIntegerField()

    license = models.CharField(max_length=50, choices=LICENSES)
    rotation = models.PositiveSmallIntegerField(
        default=0,
        help_text=(
            "Current clockwise rotation, in degrees, by which the smaller image sizes "
            "differ from the original image."
        ),
    )
    original_format = models.CharField(max_length=10, help_text="eg, 'png'")
    safety_level = models.PositiveSmallIntegerField(
        default=SAFETY_LEVELS[0][0], choices=SAFETY_LEVELS
    )

    has_people = models.BooleanField(
        default=False, help_text="Are there Flickr users in this photo?"
    )

    last_update_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "The last time the photo, or any of its metadata (tags, comments, etc.) "
            "was modified on Flickr. UTC."
        ),
    )
    taken_time = models.DateTimeField(
        null=True, blank=True, help_text="In the Flickr user's timezone."
    )
    taken_granularity = models.PositiveSmallIntegerField(
        default=DATE_GRANULARITIES[0][0], choices=DATE_GRANULARITIES
    )
    taken_unknown = models.BooleanField(default=False)
    taken_year = models.PositiveSmallIntegerField(
        null=True, blank=True, db_index=True, help_text="Set automatically on save"
    )

    view_count = models.PositiveIntegerField(
        default=0, help_text="How many times this had been viewed when fetched"
    )
    comment_count = models.PositiveIntegerField(
        default=0, help_text="How many comments this had when fetched"
    )

    media = models.CharField(
        default=MEDIA_TYPES[0][0], choices=MEDIA_TYPES, max_length=10
    )

    # SIZES ##################################################################

    sizes_raw = models.TextField(
        blank=True, help_text="The raw JSON from the API - flickr.photos.getSizes."
    )

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
    x_large_3k_width = models.PositiveSmallIntegerField(null=True, blank=True)
    x_large_3k_height = models.PositiveSmallIntegerField(null=True, blank=True)
    x_large_4k_width = models.PositiveSmallIntegerField(null=True, blank=True)
    x_large_4k_height = models.PositiveSmallIntegerField(null=True, blank=True)
    x_large_5k_width = models.PositiveSmallIntegerField(null=True, blank=True)
    x_large_5k_height = models.PositiveSmallIntegerField(null=True, blank=True)
    x_large_6k_width = models.PositiveSmallIntegerField(null=True, blank=True)
    x_large_6k_height = models.PositiveSmallIntegerField(null=True, blank=True)
    original_width = models.PositiveSmallIntegerField(null=True, blank=True)
    original_height = models.PositiveSmallIntegerField(null=True, blank=True)

    # Video sizes; when media='video'.
    mobile_mp4_width = models.PositiveSmallIntegerField(
        "Mobile MP4 width", null=True, blank=True
    )
    mobile_mp4_height = models.PositiveSmallIntegerField(
        "Mobile MP4 height", null=True, blank=True
    )
    site_mp4_width = models.PositiveSmallIntegerField(
        "Site MP4 width", null=True, blank=True
    )
    site_mp4_height = models.PositiveSmallIntegerField(
        "Site MP4 height", null=True, blank=True
    )
    hd_mp4_width = models.PositiveSmallIntegerField(
        "HD MP4 width", null=True, blank=True
    )
    hd_mp4_height = models.PositiveSmallIntegerField(
        "HD MP4 height", null=True, blank=True
    )
    video_original_width = models.PositiveSmallIntegerField(null=True, blank=True)
    video_original_height = models.PositiveSmallIntegerField(null=True, blank=True)

    # LOCATION ###############################################################

    geo_is_private = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="If true, the Photo's location info should not be displayed.",
    )

    # https://www.flickr.com/services/api/flickr.photos.search.html
    location_accuracy = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        default=1,
        help_text=(
            "World is 1; Country is ~3; Region is ~6; City is ~11; Street is ~16."
        ),
    )
    # https://www.flickr.com/services/api/flickr.photos.search.html
    location_context = models.PositiveSmallIntegerField(
        default=LOCATION_CONTEXTS[0][0], choices=LOCATION_CONTEXTS
    )
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
    exif_raw = models.TextField(
        blank=True, help_text="The raw JSON from the API from flickr.photos.getExif."
    )
    exif_camera = models.CharField(blank=True, max_length=50)
    exif_lens_model = models.CharField(
        blank=True, max_length=50, help_text="eg, 'E PZ 16-50mm F3.5-5.6 OSS'."
    )
    exif_aperture = models.CharField(
        blank=True, max_length=30, help_text="eg, 'f/13.0'."
    )
    exif_exposure = models.CharField(
        blank=True, max_length=30, help_text="eg, '0.01 sec (1/100)'."
    )
    exif_flash = models.CharField(
        blank=True, max_length=30, help_text="eg, 'Off, Did not fire'."
    )
    exif_focal_length = models.CharField(
        blank=True, max_length=10, help_text="eg, '38 mm.'"
    )
    exif_iso = models.IntegerField(blank=True, null=True, help_text="eg, '100'.")

    # TODO: NOTES
    # TODO: PEOPLE

    tags = TaggableManager(
        blank=True, manager=managers._PhotoTaggableManager, through=TaggedPhoto
    )

    def upload_path(self, filename):
        "Make path under MEDIA_ROOT where original files will be saved."
        # If NSID is '35034346050@N01', get '35034346050'
        nsid = self.user.nsid[: self.user.nsid.index("@")]

        # If NSID is '35034346050@N01'
        # then, 'flickr/60/50/35034346050/avatars/avatar_name.jpg'
        return "/".join(
            [
                app_settings.FLICKR_DIR_BASE,
                nsid[-4:-2],
                nsid[-2:],
                self.user.nsid.replace("@", ""),
                "photos",
                str(
                    self.taken_time.date().strftime(
                        app_settings.FLICKR_DIR_PHOTOS_FORMAT
                    )
                ),
                filename,
            ]
        )

    original_file = models.ImageField(
        upload_to=upload_path, null=False, blank=True, default=""
    )
    video_original_file = models.FileField(
        upload_to=upload_path,
        null=False,
        blank=True,
        default="",
        help_text="Only present for Videos.",
    )

    class Meta:
        ordering = ("-post_time",)

    def save(self, *args, **kwargs):
        if self.taken_time:
            self.taken_year = self.taken_time.year
        else:
            self.taken_year = None
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "flickr:photo_detail",
            kwargs={"nsid": self.user.nsid, "flickr_id": self.flickr_id},
        )

    def get_next_public_by_post_time(self):
        "The next public Photo by this User, ordered by post_time."
        try:
            return (
                Photo.public_photo_objects.filter(
                    post_time__gte=self.post_time, user=self.user
                )
                .exclude(pk=self.pk)
                .order_by("post_time")[:1]
                .get()
            )
        except Exception:
            pass

    def get_previous_public_by_post_time(self):
        "The previous public Photo by this User, ordered by post_time."
        try:
            return (
                Photo.public_photo_objects.filter(
                    post_time__lte=self.post_time, user=self.user
                )
                .exclude(pk=self.pk)
                .order_by("-post_time")[:1]
                .get()
            )
        except Exception:
            pass

    # Shortcuts:
    def get_next(self):
        return self.get_next_public_by_post_time()

    def get_previous(self):
        return self.get_previous_public_by_post_time()

    @property
    def account(self):
        "The Account whose photo this is, if any. Otherwise, None."
        try:
            return self.user.account_set.all()[0]
        except IndexError:
            return None

    @property
    def safety_level_str(self):
        "Returns the text version of the safety_level, eg 'Restricted'."
        levels = dict((x, y) for x, y in self.SAFETY_LEVELS)

        try:
            return levels[self.safety_level]
        except KeyError:
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
        return ", ".join(filter(None, strs))

    @property
    def has_exif(self):
        "Do we have any EXIF info to display?"
        props = [
            "exif_camera",
            "exif_lens_model",
            "exif_aperture",
            "exif_exposure",
            "exif_flash",
            "exif_focal_length",
            "exif_iso",
        ]
        has_exif = False

        for prop in props:
            if getattr(self, prop):
                has_exif = True
                break

        return has_exif

    # Properties for always-the-same widths/heights, to maintain consistency:

    @property
    def square_width(self):
        return 75

    @property
    def square_height(self):
        return 75

    @property
    def large_square_width(self):
        return 150

    @property
    def large_square_height(self):
        return 150

    @property
    def remote_original_url(self):
        """
        URL of the original image file on Flickr.com.
        Usually we'd use self.original_url but if we have
        FLICKR_USE_LOCAL_MEDIA as True, then we still need to be able
        to get the remote original file URL somehow. So use this.
        """
        return self._remote_image_url("original")

    @property
    def remote_video_original_url(self):
        """
        Same as remote_original_url but for video.
        EXCEPT currently we can ONLY get the remote video URLs anyway.
        """
        return self._remote_video_url("video_original")

    def _image_url(self, size):
        """
        Helper for the photo url property methods.
        See https://www.flickr.com/services/api/misc.urls.html
        size -- One of the keys from self.PHOTO_SIZES.
        """
        if app_settings.FLICKR_USE_LOCAL_MEDIA:
            return self._local_image_url(size)
        else:
            return self._remote_image_url(size)

    def _local_image_url(self, size):
        """
        Generate the URL of an image of a particular size, hosted locally,
        based on the original file (which must already be downloaded).
        """
        if self.original_file:
            if size == "original":
                return self.original_file.url
            else:
                generator = self.PHOTO_SIZES[size]["generator"]
                try:
                    image_generator = generator(source=self.original_file)
                    result = ImageCacheFile(image_generator)
                    return result.url
                except Exception:
                    # We have an original file but something's wrong with it.
                    # Might be 0 bytes or something.
                    return static("ditto-core/img/original_error.jpg")
        else:
            # We haven't downloaded an original file for this Photo.
            return static("ditto-core/img/original_missing.jpg")

    def _remote_image_url(self, size):
        """
        Generate the URL of an image of a particular size, on flickr.com.
        size -- One of the keys from self.PHOTO_SIZES.
        """
        if size == "original":
            return "https://farm%s.static.flickr.com/%s/%s_%s_%s.%s" % (
                self.farm,
                self.server,
                self.flickr_id,
                self.original_secret,
                self.PHOTO_SIZES["original"]["suffix"],
                self.original_format,
            )
        else:
            size_ext = ""
            # Medium size doesn't have a letter suffix.
            if self.PHOTO_SIZES[size]["suffix"]:
                size_ext = "_%s" % self.PHOTO_SIZES[size]["suffix"]
            return "https://farm%s.static.flickr.com/%s/%s_%s%s.jpg" % (
                self.farm,
                self.server,
                self.flickr_id,
                self.secret,
                size_ext,
            )

    def _video_url(self, size):
        return self._remote_video_url(size)

    # def _local_video_url(self, size):
    # """One day, if we work out how to translate our downloaded original
    # video files into something usable on the web in different sizes, then
    # we can have _video_url() call this if
    # app_settings.FLICKR_USE_LOCAL_MEDIA is False.
    # """
    # pass

    def _remote_video_url(self, size):
        """
        Helper for the video URL property methods, on Flickr.com.
        Returns None for photos, or a URL for videos like:
        https://www.flickr.com/photos/philgyford/25743649964/play/site/a8bd5ddf59/
        size -- One of the keys from self.VIDEO_SIZES.
        """
        if self.media == "photo":
            return None
        else:
            if size == "video_original":
                secret = self.original_secret
            else:
                secret = self.secret
            url_size = self.VIDEO_SIZES[size]["url_size"]
            return "%splay/%s/%s/" % (self.permalink, url_size, secret)

    def __getattr__(self, name):
        """
        Enables us to use properties like 'small_320_url' or 'site_mp4_url'.
        Will call the correct internal helper method to return the URL.
        """
        try:
            # Split 'small_240_url' into ['small_240', 'url']
            size, attr = name.rsplit("_", 1)
        except ValueError:
            self._raise_attr_error(type(self).__name__, name)

        if attr == "url":
            # eg video_original_url()
            if size in self.VIDEO_SIZES:
                return self._video_url(size)
            elif size in self.PHOTO_SIZES:
                return self._image_url(size)
            else:
                self._raise_attr_error(type(self).__name__, name)
        else:
            self._raise_attr_error(type(self).__name__, name)

    def _raise_attr_error(self, obj, attr):
        msg = "'{0}' object has no attribute '{1}'"
        raise AttributeError(msg.format(obj, attr))

    def _summary_source(self):
        "Used to make the `summary` property."
        return self.description


class Photoset(TimeStampedModelMixin, DiffModelMixin, models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    flickr_id = models.BigIntegerField(
        null=False, blank=False, unique=True, db_index=True
    )
    primary_photo = models.ForeignKey(
        "Photo", on_delete=models.SET_NULL, null=True, related_name="primary_photosets"
    )
    title = models.CharField(null=False, blank=False, max_length=255)
    description = models.TextField(null=False, blank=True, help_text="Can contain HTML")
    photo_count = models.PositiveIntegerField(
        null=False,
        blank=False,
        default=0,
        help_text="The number of photos in the set on Flickr",
    )
    video_count = models.PositiveIntegerField(
        null=False,
        blank=False,
        default=0,
        help_text="The number of videos in the set on Flickr",
    )
    view_count = models.PositiveIntegerField(
        default=0, help_text="How many times this had been viewed when fetched"
    )
    comment_count = models.PositiveIntegerField(
        default=0, help_text="How many comments this had when fetched"
    )

    last_update_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The last time the set was modified on Flickr. UTC.",
    )
    flickr_created_time = models.DateTimeField(
        null=True, blank=True, help_text="When the set was created on Flickr. UTC."
    )

    fetch_time = models.DateTimeField(
        null=True, blank=True, help_text="The time the item's data was last fetched."
    )
    raw = models.TextField(blank=True, help_text="The raw JSON from the API.")
    photos_raw = models.TextField(
        blank=True, help_text="The raw JSON from the API listing the photos."
    )

    # Returns ALL photos, public AND private.
    photos = SortedManyToManyField("Photo", related_name="photosets")

    def public_photos(self):
        "Returns only public photos."
        return self.photos.filter(is_private=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-flickr_created_time"]

    def get_absolute_url(self):
        return reverse(
            "flickr:photoset_detail",
            kwargs={"nsid": self.user.nsid, "flickr_id": self.flickr_id},
        )

    @property
    def permalink(self):
        return "https://www.flickr.com/photos/%s/albums/%s" % (
            self.user.nsid,
            self.flickr_id,
        )


class User(TimeStampedModelMixin, DiffModelMixin, models.Model):
    nsid = models.CharField(
        null=False,
        blank=False,
        unique=True,
        db_index=True,
        max_length=50,
        verbose_name="NSID",
    )
    is_pro = models.BooleanField(
        null=False, blank=False, default=False, verbose_name="Is Pro?"
    )
    iconserver = models.PositiveIntegerField(null=False, blank=False, default=0)
    iconfarm = models.PositiveIntegerField(null=False, blank=False)

    username = models.CharField(null=False, blank=False, unique=True, max_length=50)
    realname = models.CharField(null=False, blank=False, max_length=255)
    location = models.CharField(null=False, blank=True, max_length=255)
    description = models.TextField(null=False, blank=True, help_text="May contain HTML")

    photos_url = models.URLField(
        null=False, blank=False, max_length=255, verbose_name="Photos URL at Flickr"
    )
    profile_url = models.URLField(
        null=False, blank=False, max_length=255, verbose_name="Avatar URL on Flickr"
    )

    photos_count = models.PositiveIntegerField(null=False, blank=False, default=0)
    photos_views = models.PositiveIntegerField(null=False, blank=False, default=0)
    photos_first_date = models.DateTimeField(null=True, blank=False)
    photos_first_date_taken = models.DateTimeField(null=True, blank=False)

    # As on DittoItemModel:
    fetch_time = models.DateTimeField(
        null=True, blank=True, help_text="The time the data was last fetched."
    )
    raw = models.TextField(
        null=False, blank=True, help_text="The raw JSON from the API."
    )
    timezone_id = models.CharField(
        null=False, blank=False, max_length=50, help_text="eg, 'Europe/London'."
    )

    def avatar_upload_path(self, filename):
        "Make path under MEDIA_ROOT where avatar file will be saved."
        # If NSID is '35034346050@N01', get '35034346050'
        nsid = self.nsid[: self.nsid.index("@")]

        # If NSID is '35034346050@N01'
        # then, 'flickr/60/50/35034346050/avatars/avatar_name.jpg'
        return "/".join(
            [
                app_settings.FLICKR_DIR_BASE,
                nsid[-4:-2],
                nsid[-2:],
                self.nsid.replace("@", ""),
                "avatars",
                filename,
            ]
        )

    avatar = models.ImageField(
        upload_to=avatar_upload_path, null=False, blank=True, default=""
    )

    objects = models.Manager()
    # All Users that have Accounts:
    objects_with_accounts = managers.WithAccountsManager()

    def __str__(self):
        return self.realname

    class Meta:
        ordering = ["realname"]

    def get_absolute_url(self):
        return reverse("flickr:user_detail", kwargs={"nsid": self.nsid})

    @property
    def name(self):
        return self.realname

    @property
    def permalink(self):
        return self.photos_url

    @property
    def avatar_url(self):
        try:
            return self.avatar.url
        except ValueError:
            return static("ditto-core/img/default_avatar.png")

    @property
    def original_icon_url(self):
        """URL of the avatar/profile pic at Flickr."""
        if self.iconserver:
            return "https://farm%s.staticflickr.com/%s/buddyicons/%s.jpg" % (
                self.iconfarm,
                self.iconserver,
                self.nsid,
            )
        else:
            return "https://www.flickr.com/images/buddyicon.gif"
