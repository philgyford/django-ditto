import django.db.models.deletion
import taggit.managers
from django.db import migrations, models

import ditto.core.models


class Migration(migrations.Migration):

    dependencies = [
        ("taggit", "0002_auto_20150616_2121"),
    ]

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
                        auto_created=True,
                    ),
                ),
                (
                    "time_created",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="The time this item was created in the database.",
                    ),
                ),
                (
                    "time_modified",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="The time this item was last saved to the database.",
                    ),
                ),
                (
                    "api_key",
                    models.CharField(
                        max_length=255, blank=True, verbose_name="API Key"
                    ),
                ),
                (
                    "api_secret",
                    models.CharField(
                        max_length=255, blank=True, verbose_name="API Secret"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True, help_text="If false, new Photos won't be fetched."
                    ),
                ),
            ],
            options={"ordering": ["user__realname"]},
        ),
        migrations.CreateModel(
            name="Photo",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
                        auto_created=True,
                    ),
                ),
                (
                    "time_created",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="The time this item was created in the database.",
                    ),
                ),
                (
                    "time_modified",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="The time this item was last saved to the database.",
                    ),
                ),
                ("title", models.CharField(max_length=255, blank=True)),
                (
                    "permalink",
                    models.URLField(
                        blank=True,
                        help_text="URL of the item on the service's website.",
                    ),
                ),
                (
                    "summary",
                    models.CharField(
                        max_length=255,
                        blank=True,
                        help_text="eg, Initial text of a blog post, start of the description of a photo, all of a Tweet's text, etc. No HTML.",  # noqa: E501
                    ),
                ),
                (
                    "is_private",
                    models.BooleanField(
                        default=False,
                        help_text="If true, this item will not be shown on public-facing pages.",  # noqa: E501
                    ),
                ),
                (
                    "fetch_time",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="The time the item's data was last fetched, and was new or changed.",  # noqa: E501
                    ),
                ),
                (
                    "post_time",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="The time the item was originally posted/created on its service.",  # noqa: E501
                    ),
                ),
                (
                    "latitude",
                    models.DecimalField(
                        null=True, blank=True, decimal_places=9, max_digits=12
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        null=True, blank=True, decimal_places=9, max_digits=12
                    ),
                ),
                (
                    "raw",
                    models.TextField(
                        blank=True, help_text="eg, the raw JSON from the API."
                    ),
                ),
                (
                    "flickr_id",
                    models.BigIntegerField(
                        help_text="ID of this photo on Flickr.",
                        db_index=True,
                        unique=True,
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, help_text="Can contain HTML"),
                ),
                ("secret", models.CharField(max_length=20)),
                ("original_secret", models.CharField(max_length=20)),
                ("server", models.CharField(max_length=20)),
                ("farm", models.PositiveSmallIntegerField()),
                (
                    "license",
                    models.CharField(
                        max_length=50,
                        choices=[
                            ("0", "All Rights Reserved"),
                            ("1", "Attribution-NonCommercial-ShareAlike License"),
                            ("2", "Attribution-NonCommercial License"),
                            ("3", "Attribution-NonCommercial-NoDerivs License"),
                            ("4", "Attribution License"),
                            ("5", "Attribution-ShareAlike License"),
                            ("6", "Attribution-NoDerivs License"),
                            ("7", "No known copyright restrictions"),
                            ("8", "United States Government Work"),
                        ],
                    ),
                ),
                (
                    "rotation",
                    models.PositiveSmallIntegerField(
                        help_text="Current clockwise rotation, in degrees, by which the smaller image sizes differ from the original image.",  # noqa: E501
                        default=0,
                    ),
                ),
                (
                    "original_format",
                    models.CharField(max_length=10, help_text="eg, 'png'"),
                ),
                (
                    "safety_level",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, "none"),
                            (1, "Safe"),
                            (2, "Moderate"),
                            (3, "Restricted"),
                        ],
                        default=0,
                    ),
                ),
                (
                    "has_people",
                    models.BooleanField(
                        default=False, help_text="Are there Flickr users in this photo?"
                    ),
                ),
                (
                    "last_update_time",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="The last time the photo, or any of its metadata (tags, comments, etc.) was modified on Flickr. UTC.",  # noqa: E501
                    ),
                ),
                (
                    "taken_time",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="In the Flickr user's timezone.",
                    ),
                ),
                (
                    "taken_granularity",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, "Y-m-d H:i:s"),
                            (4, "Y-m"),
                            (6, "Y"),
                            (8, "Circa..."),
                        ],
                        default=0,
                    ),
                ),
                ("taken_unknown", models.BooleanField(default=False)),
                (
                    "view_count",
                    models.PositiveIntegerField(
                        help_text="How many times this had been viewed when fetched",
                        default=0,
                    ),
                ),
                (
                    "comment_count",
                    models.PositiveIntegerField(
                        help_text="How many comments this had been when fetched",
                        default=0,
                    ),
                ),
                (
                    "media",
                    models.CharField(
                        max_length=10,
                        choices=[("photo", "Photo"), ("video", "Video")],
                        default="photo",
                    ),
                ),
                (
                    "sizes_raw",
                    models.TextField(
                        blank=True,
                        help_text="eg, the raw JSON from the API - flickr.photos.getSizes.",  # noqa: E501
                    ),
                ),
                (
                    "width_t",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Thumbnail width"
                    ),
                ),
                (
                    "height_t",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Thumbnail height"
                    ),
                ),
                (
                    "width_m",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Small width"
                    ),
                ),
                (
                    "height_m",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Small height"
                    ),
                ),
                (
                    "width_n",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Small 320 width"
                    ),
                ),
                (
                    "height_n",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Small 320 height"
                    ),
                ),
                (
                    "width",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Medium width"
                    ),
                ),
                (
                    "height",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Medium height"
                    ),
                ),
                (
                    "width_z",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Medium 640 width"
                    ),
                ),
                (
                    "height_z",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Medium 640 height"
                    ),
                ),
                (
                    "width_c",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Medium 800 width"
                    ),
                ),
                (
                    "height_c",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Medium 800 height"
                    ),
                ),
                (
                    "width_b",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Large width"
                    ),
                ),
                (
                    "height_b",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Large height"
                    ),
                ),
                (
                    "width_h",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Large 1600 width"
                    ),
                ),
                (
                    "height_h",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Large 1600 height"
                    ),
                ),
                (
                    "width_k",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Large 2048 width"
                    ),
                ),
                (
                    "height_k",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Large 2048 height"
                    ),
                ),
                (
                    "width_o",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Original width"
                    ),
                ),
                (
                    "height_o",
                    models.PositiveSmallIntegerField(
                        null=True, blank=True, verbose_name="Original height"
                    ),
                ),
                (
                    "geo_is_private",
                    models.BooleanField(
                        default=False,
                        help_text="If true, the Photo's location info should not be displayed.",  # noqa: E501
                    ),
                ),
                (
                    "location_accuracy",
                    models.PositiveSmallIntegerField(
                        null=True,
                        blank=True,
                        default=1,
                        help_text="World is 1; Country is ~3; Region is ~6; City is ~11; Street is ~16.",  # noqa: E501
                    ),
                ),
                (
                    "location_context",
                    models.PositiveSmallIntegerField(
                        choices=[(0, "not defined"), (1, "indoors"), (2, "outdoors")],
                        default=0,
                    ),
                ),
                ("location_place_id", models.CharField(max_length=30, blank=True)),
                ("location_woeid", models.CharField(max_length=30, blank=True)),
                ("locality_name", models.CharField(max_length=255, blank=True)),
                ("locality_place_id", models.CharField(max_length=30, blank=True)),
                ("locality_woeid", models.CharField(max_length=30, blank=True)),
                ("county_name", models.CharField(max_length=255, blank=True)),
                ("county_place_id", models.CharField(max_length=30, blank=True)),
                ("county_woeid", models.CharField(max_length=30, blank=True)),
                ("region_name", models.CharField(max_length=255, blank=True)),
                ("region_place_id", models.CharField(max_length=30, blank=True)),
                ("region_woeid", models.CharField(max_length=30, blank=True)),
                ("country_name", models.CharField(max_length=255, blank=True)),
                ("country_place_id", models.CharField(max_length=30, blank=True)),
                ("country_woeid", models.CharField(max_length=30, blank=True)),
                (
                    "exif_raw",
                    models.TextField(
                        blank=True,
                        help_text="The raw JSON from the API from flickr.photos.getExif.",  # noqa: E501
                    ),
                ),
                ("exif_camera", models.CharField(max_length=50, blank=True)),
                (
                    "exif_lens_model",
                    models.CharField(
                        max_length=50,
                        blank=True,
                        help_text="eg, 'E PZ 16-50mm F3.5-5.6 OSS'.",
                    ),
                ),
                (
                    "exif_aperture",
                    models.CharField(
                        max_length=30, blank=True, help_text="eg, 'f/13.0'."
                    ),
                ),
                (
                    "exif_exposure",
                    models.CharField(
                        max_length=30, blank=True, help_text="eg, '0.01 sec (1/100)'."
                    ),
                ),
                (
                    "exif_flash",
                    models.CharField(
                        max_length=30, blank=True, help_text="eg, 'Off, Did not fire'."
                    ),
                ),
                (
                    "exif_focal_length",
                    models.CharField(
                        max_length=10, blank=True, help_text="eg, '38 mm.'"
                    ),
                ),
                ("exif_iso", models.IntegerField(blank=True, help_text="eg, '100'.")),
            ],
            options={"ordering": ("-taken_time",)},
            bases=(ditto.core.models.DiffModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name="TaggedPhoto",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
                        auto_created=True,
                    ),
                ),
                (
                    "flickr_id",
                    models.CharField(
                        max_length=200,
                        help_text="The tag's ID on Flickr",
                        verbose_name="Flickr ID",
                    ),
                ),
                ("machine_tag", models.BooleanField(default=False)),
            ],
            options={"verbose_name": "Photo/Tag Relationship"},
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
                        auto_created=True,
                    ),
                ),
                (
                    "time_created",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="The time this item was created in the database.",
                    ),
                ),
                (
                    "time_modified",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="The time this item was last saved to the database.",
                    ),
                ),
                (
                    "nsid",
                    models.CharField(max_length=50, verbose_name="NSID", unique=True),
                ),
                ("is_pro", models.BooleanField(verbose_name="Is Pro?", default=False)),
                ("iconserver", models.CharField(max_length=20)),
                ("iconfarm", models.PositiveIntegerField()),
                ("username", models.CharField(max_length=50, unique=True)),
                ("realname", models.CharField(max_length=255)),
                ("location", models.CharField(max_length=255, blank=True)),
                (
                    "description",
                    models.TextField(blank=True, help_text="May contain HTML"),
                ),
                (
                    "photos_url",
                    models.URLField(max_length=255, verbose_name="Photos URL"),
                ),
                (
                    "profile_url",
                    models.URLField(max_length=255, verbose_name="Profile URL"),
                ),
                ("photos_count", models.PositiveIntegerField(default=0)),
                ("photos_views", models.PositiveIntegerField(default=0)),
                ("photos_first_date", models.DateTimeField(null=True)),
                ("photos_first_date_taken", models.DateTimeField(null=True)),
                (
                    "fetch_time",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="The time the data was last fetched, and was new or changed.",  # noqa: E501
                    ),
                ),
                (
                    "raw",
                    models.TextField(
                        blank=True, help_text="eg, the raw JSON from the API."
                    ),
                ),
                (
                    "timezone_id",
                    models.CharField(max_length=50, help_text="eg, 'Europe/London'."),
                ),
            ],
            options={"ordering": ["realname"]},
            bases=(ditto.core.models.DiffModelMixin, models.Model),
        ),
        migrations.AddField(
            model_name="taggedphoto",
            name="author",
            field=models.ForeignKey(to="flickr.User", on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name="taggedphoto",
            name="content_object",
            field=models.ForeignKey(
                to="flickr.Photo",
                related_name="flickr_taggedphoto_items",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="taggedphoto",
            name="tag",
            field=models.ForeignKey(
                to="taggit.Tag",
                related_name="flickr_taggedphoto_items",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="photo",
            name="tags",
            field=taggit.managers.TaggableManager(
                blank=True,
                to="taggit.Tag",
                verbose_name="Tags",
                help_text="A comma-separated list of tags.",
                through="flickr.TaggedPhoto",
            ),
        ),
        migrations.AddField(
            model_name="photo",
            name="user",
            field=models.ForeignKey(to="flickr.User", on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name="account",
            name="user",
            field=models.ForeignKey(
                null=True,
                blank=True,
                to="flickr.User",
                on_delete=django.db.models.deletion.SET_NULL,
            ),
        ),
    ]
