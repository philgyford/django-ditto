# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flickr', '0004_auto_20160414_1120'),
    ]

    operations = [
        migrations.RenameField(
            model_name='photo',
            old_name='height_mp4_hd',
            new_name='hd_mp4_height',
        ),
        migrations.RenameField(
            model_name='photo',
            old_name='width_mp4_hd',
            new_name='hd_mp4_width',
        ),
        migrations.RenameField(
            model_name='photo',
            old_name='height_mp4_mobile',
            new_name='mobile_mp4_height',
        ),
        migrations.RenameField(
            model_name='photo',
            old_name='width_mp4_mobile',
            new_name='mobile_mp4_width',
        ),
        migrations.RenameField(
            model_name='photo',
            old_name='height_mp4_site',
            new_name='site_mp4_height',
        ),
        migrations.RenameField(
            model_name='photo',
            old_name='width_mp4_site',
            new_name='site_mp4_width',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='height',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='height_b',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='height_c',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='height_h',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='height_k',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='height_m',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='height_n',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='height_o',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='height_t',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='height_video_original',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='height_z',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='width',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='width_b',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='width_c',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='width_h',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='width_k',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='width_m',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='width_n',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='width_o',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='width_t',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='width_video_original',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='width_z',
        ),
        migrations.AddField(
            model_name='photo',
            name='large_1600_height',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='large_1600_width',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='large_2400_width',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='large_2400_height',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='large_height',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='large_width',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='medium_640_height',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='medium_640_width',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='medium_800_height',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='medium_800_width',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='medium_height',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='medium_width',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='original_height',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='original_width',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='small_320_height',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='small_320_width',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='small_height',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='small_width',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='thumbnail_height',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='thumbnail_width',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='video_original_height',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='video_original_width',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
    ]
