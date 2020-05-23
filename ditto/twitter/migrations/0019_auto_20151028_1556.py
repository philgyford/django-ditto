# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0018_tweet_text_html"),
    ]

    operations = [
        migrations.CreateModel(
            name="Photo",
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
                ("twitter_id", models.BigIntegerField(unique=True)),
                ("media_url", models.URLField(help_text="URL of the image itself")),
                (
                    "page_url",
                    models.URLField(help_text="URL of its page on Twitter.com"),
                ),
                (
                    "is_private",
                    models.BooleanField(
                        default=False,
                        help_text="If true, this item will not be shown on public-facing pages.",  # noqa: E501
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
            ],
            options={"ordering": ["time_created"]},
        ),
        migrations.AddField(
            model_name="tweet",
            name="photos_count",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Number of Photos attached to this Tweet",
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="tweet",
            name="is_private",
            field=models.BooleanField(
                default=False,
                help_text="If true, this item will not be shown on public-facing pages.",  # noqa: E501
            ),
        ),
        migrations.AddField(
            model_name="photo",
            name="tweet",
            field=models.ForeignKey(to="twitter.Tweet", on_delete=models.CASCADE),
        ),
    ]
