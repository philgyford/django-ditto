# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flickr', '0003_auto_20160413_0906'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='height_mp4_hd',
            field=models.PositiveSmallIntegerField(null=True, verbose_name='HD MP4 height', blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='height_mp4_mobile',
            field=models.PositiveSmallIntegerField(null=True, verbose_name='Mobile MP4 height', blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='height_mp4_site',
            field=models.PositiveSmallIntegerField(null=True, verbose_name='Site MP4 height', blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='height_video_original',
            field=models.PositiveSmallIntegerField(null=True, verbose_name='Original video height', blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='width_mp4_hd',
            field=models.PositiveSmallIntegerField(null=True, verbose_name='HD MP4 width', blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='width_mp4_mobile',
            field=models.PositiveSmallIntegerField(null=True, verbose_name='Mobile MP4 width', blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='width_mp4_site',
            field=models.PositiveSmallIntegerField(null=True, verbose_name='Site MP4 width', blank=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='width_video_original',
            field=models.PositiveSmallIntegerField(null=True, verbose_name='Original video width', blank=True),
        ),
        migrations.AlterField(
            model_name='photo',
            name='license',
            field=models.CharField(choices=[('0', 'All Rights Reserved'), ('1', 'Attribution-NonCommercial-ShareAlike License'), ('2', 'Attribution-NonCommercial License'), ('3', 'Attribution-NonCommercial-NoDerivs License'), ('4', 'Attribution License'), ('5', 'Attribution-ShareAlike License'), ('6', 'Attribution-NoDerivs License'), ('7', 'No known copyright restrictions'), ('8', 'United States Government Work'), ('9', 'Public Domain Dedication (CC0)'), ('10', 'Public Domain Mark'), ('11', 'Unused'), ('12', 'Unused'), ('13', 'Unused'), ('14', 'Unused'), ('15', 'Unused'), ('16', 'Unused'), ('17', 'Unused'), ('18', 'Unused'), ('19', 'Unused'), ('20', 'Unused')], max_length=50),
        ),
        migrations.AlterField(
            model_name='photo',
            name='taken_granularity',
            field=models.PositiveSmallIntegerField(default=0, choices=[(0, 'Y-m-d H:i:s'), (1, 'Unused'), (2, 'Unused'), (3, 'Unused'), (4, 'Y-m'), (5, 'Unused'), (6, 'Y'), (7, 'Unused'), (8, 'Circa...'), (9, 'Unused'), (10, 'Unused')]),
        ),
    ]
