# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pinboard', '0010_auto_20150730_1112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='api_token',
            field=models.CharField(help_text='From https://pinboard.in/settings/password eg, "philgyford:1234567890ABCDEFGHIJ"', max_length=51),
        ),
        migrations.AlterField(
            model_name='account',
            name='time_created',
            field=models.DateTimeField(help_text='The time this item was created in the database.', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='time_modified',
            field=models.DateTimeField(help_text='The time this item was last saved to the database.', auto_now=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='url',
            field=models.URLField(unique=True, help_text="eg, 'https://pinboard.in/u:philgyford'", max_length=255),
        ),
        migrations.AlterField(
            model_name='account',
            name='username',
            field=models.CharField(unique=True, help_text="eg, 'philgyford'", max_length=30),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='description',
            field=models.TextField(help_text="The 'extended' text description.", blank=True),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='fetch_time',
            field=models.DateTimeField(help_text="The time the item's data was last fetched, and was new or changed.", null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='is_private',
            field=models.BooleanField(help_text='If set, this item will not be shown on public-facing pages.', default=False),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='permalink',
            field=models.URLField(help_text="URL of the item on the service's website.", blank=True),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='post_time',
            field=models.DateTimeField(help_text='The time this was created on Pinboard.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='raw',
            field=models.TextField(help_text='eg, the raw JSON from the API.', blank=True),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='summary',
            field=models.CharField(help_text="eg, Initial text of a blog post, start of the description of a photo, all of a Tweet's text, etc. No HTML.", blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='time_created',
            field=models.DateTimeField(help_text='The time this item was created in the database.', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='time_modified',
            field=models.DateTimeField(help_text='The time this item was last saved to the database.', auto_now=True),
        ),
    ]
