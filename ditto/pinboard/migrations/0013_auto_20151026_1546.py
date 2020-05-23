# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("pinboard", "0012_account_is_active"),
    ]

    operations = [
        migrations.CreateModel(
            name="BookmarkTag",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        auto_created=True,
                        verbose_name="ID",
                        primary_key=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(unique=True, verbose_name="Name", max_length=100),
                ),
                (
                    "slug",
                    models.SlugField(unique=True, verbose_name="Slug", max_length=100),
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
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="TaggedBookmark",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        auto_created=True,
                        verbose_name="ID",
                        primary_key=True,
                    ),
                ),
                (
                    "object_id",
                    models.IntegerField(verbose_name="Object id", db_index=True),
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
                    "content_type",
                    models.ForeignKey(
                        related_name="pinboard_taggedbookmark_tagged_items",
                        to="contenttypes.ContentType",
                        verbose_name="Content type",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "tag",
                    models.ForeignKey(
                        related_name="pinboard_taggedbookmark_items",
                        to="pinboard.BookmarkTag",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.AlterField(
            model_name="bookmark",
            name="tags",
            field=taggit.managers.TaggableManager(
                verbose_name="Tags",
                through="pinboard.TaggedBookmark",
                to="pinboard.BookmarkTag",
                help_text="A comma-separated list of tags.",
            ),
        ),
    ]
