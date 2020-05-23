# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0032_auto_20160414_1637"),
    ]

    operations = [
        migrations.AlterField(
            model_name="media",
            name="aspect_ratio",
            field=models.CharField(
                help_text='eg, "4:3" or "16:9"', max_length=5, blank=True
            ),
        ),
        migrations.AlterField(
            model_name="media",
            name="dash_url",
            field=models.URLField(verbose_name="MPEG-DASH URL", default="", blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="media",
            name="mp4_bitrate_1",
            field=models.PositiveIntegerField(
                help_text="Lowest bitrate",
                null=True,
                verbose_name="MP4 Bitrate (1)",
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="media",
            name="mp4_bitrate_2",
            field=models.PositiveIntegerField(
                help_text="Medium bitrate",
                null=True,
                verbose_name="MP4 Bitrate (2)",
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="media",
            name="mp4_bitrate_3",
            field=models.PositiveIntegerField(
                help_text="Highest bitrate",
                null=True,
                verbose_name="MP4 Bitrate (3)",
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="media",
            name="mp4_url_1",
            field=models.URLField(
                help_text="Lowest bitrate",
                verbose_name="MP4 URL (1)",
                default="",
                blank=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="media",
            name="mp4_url_2",
            field=models.URLField(
                help_text="Medium bitrate",
                verbose_name="MP4 URL (2)",
                default="",
                blank=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="media",
            name="mp4_url_3",
            field=models.URLField(
                help_text="Highest bitrate",
                verbose_name="MP4 URL (3)",
                default="",
                blank=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="media",
            name="webm_url",
            field=models.URLField(verbose_name="WebM URL", default="", blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="media",
            name="xmpeg_url",
            field=models.URLField(verbose_name="X-MPEG URL", default="", blank=True),
            preserve_default=False,
        ),
    ]
