# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('time_modified', models.DateTimeField(auto_now=True)),
                ('username', models.CharField(help_text=b"eg, 'philgyford'", unique=True, max_length=30)),
                ('url', models.URLField(help_text=b"eg, 'https://pinboard.in/u:philgyford'", max_length=255)),
                ('api_token', models.CharField(help_text=b'From https://pinboard.in/settings/password eg, "philgyford:1234567890ABCDEFGHIJ"', max_length=51)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Bookmark',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('time_modified', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=255, blank=True)),
                ('permalink', models.URLField(help_text=b"URL of the item on the service's website.", blank=True)),
                ('summary', models.TextField(help_text=b"eg, First paragraph of a blog post, start of the description of a photo, all of a Tweet's text, etc.", blank=True)),
                ('is_private', models.BooleanField(default=False, help_text=b'If True, this item should NOT be shown on public-facing pages.')),
                ('fetch_time', models.DateTimeField(help_text=b'The time the Raw data was last fetched.', null=True, blank=True)),
                ('raw', models.TextField(help_text=b'The raw JSON from the API.', blank=True)),
                ('url', models.TextField(unique=True, validators=[django.core.validators.URLValidator()])),
                ('post_time', models.DateTimeField()),
                ('description', models.TextField(help_text=b"The 'extended' text description.", blank=True)),
                ('to_read', models.BooleanField(default=False)),
                ('shared', models.BooleanField(default=True)),
                ('account', models.ForeignKey(to='pinboard.Account')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
