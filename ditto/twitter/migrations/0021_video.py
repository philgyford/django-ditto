# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0020_auto_20151028_1611'),
    ]

    operations = [
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('time_created', models.DateTimeField(help_text='The time this item was created in the database.', auto_now_add=True)),
                ('time_modified', models.DateTimeField(help_text='The time this item was last saved to the database.', auto_now=True)),
                ('twitter_id', models.BigIntegerField(unique=True)),
                ('is_private', models.BooleanField(help_text='If true, this item will not be shown on public-facing pages.', default=False)),
                ('large_w', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Large width')),
                ('large_h', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Large height')),
                ('medium_w', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Medium width')),
                ('medium_h', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Medium height')),
                ('small_w', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Small width')),
                ('small_h', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Small height')),
                ('thumb_w', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Thumbnail width')),
                ('thumb_h', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Thumbnail height')),
                ('image_url', models.URLField(help_text='URL of an image to use as a thumbnail/preview.')),
                ('mp4_url_1', models.URLField(blank=True, null=True, verbose_name='MP4 URL (1)')),
                ('mp4_url_2', models.URLField(blank=True, null=True, verbose_name='MP4 URL (2)')),
                ('mp4_url_3', models.URLField(blank=True, null=True, verbose_name='MP4 URL (3)')),
                ('mp4_bitrate_1', models.PositiveIntegerField(blank=True, null=True, verbose_name='MP4 Bitrate (1)')),
                ('mp4_bitrate_2', models.PositiveIntegerField(blank=True, null=True, verbose_name='MP4 Bitrate (2)')),
                ('mp4_bitrate_3', models.PositiveIntegerField(blank=True, null=True, verbose_name='MP4 Bitrate (3)')),
                ('webm_url', models.URLField(blank=True, null=True, verbose_name='WebM URL')),
                ('aspect_ratio', models.CharField(help_text='eg, "4:3" or "16:9"', max_length=5)),
                ('duration', models.PositiveIntegerField(help_text='In milliseconds', blank=True, null=True)),
                ('tweet', models.ForeignKey(to='twitter.Tweet')),
            ],
            options={
                'ordering': ['time_created'],
                'abstract': False,
            },
        ),
    ]
