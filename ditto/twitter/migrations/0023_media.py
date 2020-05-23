# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0022_auto_20151104_0840"),
    ]

    operations = [
        migrations.CreateModel(
            name="Media",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        auto_created=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "time_created",
                    models.DateTimeField(
                        help_text="The time this item was created in the database.",
                        auto_now_add=True,
                    ),
                ),
                (
                    "time_modified",
                    models.DateTimeField(
                        help_text="The time this item was last saved to the database.",
                        auto_now=True,
                    ),
                ),
                (
                    "media_type",
                    models.CharField(
                        choices=[("photo", "Photo"), ("video", "Video")], max_length=8
                    ),
                ),
                ("twitter_id", models.BigIntegerField(unique=True)),
                ("image_url", models.URLField(help_text="URL of the image itself")),
                (
                    "is_private",
                    models.BooleanField(
                        help_text="If true, this item will not be shown on public-facing pages.",  # noqa: E501
                        default=False,
                    ),
                ),
                (
                    "large_w",
                    models.PositiveSmallIntegerField(
                        null=True, verbose_name="Large width", blank=True
                    ),
                ),
                (
                    "large_h",
                    models.PositiveSmallIntegerField(
                        null=True, verbose_name="Large height", blank=True
                    ),
                ),
                (
                    "medium_w",
                    models.PositiveSmallIntegerField(
                        null=True, verbose_name="Medium width", blank=True
                    ),
                ),
                (
                    "medium_h",
                    models.PositiveSmallIntegerField(
                        null=True, verbose_name="Medium height", blank=True
                    ),
                ),
                (
                    "small_w",
                    models.PositiveSmallIntegerField(
                        null=True, verbose_name="Small width", blank=True
                    ),
                ),
                (
                    "small_h",
                    models.PositiveSmallIntegerField(
                        null=True, verbose_name="Small height", blank=True
                    ),
                ),
                (
                    "thumb_w",
                    models.PositiveSmallIntegerField(
                        null=True, verbose_name="Thumbnail width", blank=True
                    ),
                ),
                (
                    "thumb_h",
                    models.PositiveSmallIntegerField(
                        null=True, verbose_name="Thumbnail height", blank=True
                    ),
                ),
                (
                    "mp4_url_1",
                    models.URLField(null=True, verbose_name="MP4 URL (1)", blank=True),
                ),
                (
                    "mp4_url_2",
                    models.URLField(null=True, verbose_name="MP4 URL (2)", blank=True),
                ),
                (
                    "mp4_url_3",
                    models.URLField(null=True, verbose_name="MP4 URL (3)", blank=True),
                ),
                (
                    "mp4_bitrate_1",
                    models.PositiveIntegerField(
                        null=True, verbose_name="MP4 Bitrate (1)", blank=True
                    ),
                ),
                (
                    "mp4_bitrate_2",
                    models.PositiveIntegerField(
                        null=True, verbose_name="MP4 Bitrate (2)", blank=True
                    ),
                ),
                (
                    "mp4_bitrate_3",
                    models.PositiveIntegerField(
                        null=True, verbose_name="MP4 Bitrate (3)", blank=True
                    ),
                ),
                (
                    "webm_url",
                    models.URLField(null=True, verbose_name="WebM URL", blank=True),
                ),
                (
                    "aspect_ratio",
                    models.CharField(help_text='eg, "4:3" or "16:9"', max_length=5),
                ),
                (
                    "duration",
                    models.PositiveIntegerField(
                        help_text="In milliseconds", null=True, blank=True
                    ),
                ),
                (
                    "tweet",
                    models.ForeignKey(to="twitter.Tweet", on_delete=models.CASCADE),
                ),
            ],
            options={"ordering": ["time_created"]},
        ),
    ]
