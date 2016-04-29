# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import ditto.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0002_auto_20150729_1704'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tweet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_created', models.DateTimeField(help_text=b'The time this item was created in the database.', auto_now_add=True)),
                ('time_modified', models.DateTimeField(help_text=b'The time this item was last saved to the database.', auto_now=True)),
                ('title', models.CharField(max_length=255, blank=True)),
                ('permalink', models.URLField(help_text=b"URL of the item on the service's website.", blank=True)),
                ('summary', models.CharField(help_text=b"eg, Initial text of a blog post, start of the description of a photo, all of a Tweet's text, etc. No HTML.", max_length=255, blank=True)),
                ('is_private', models.BooleanField(default=False, help_text=b'If set, this item will not be shown on public-facing pages.')),
                ('fetch_time', models.DateTimeField(help_text=b"The time the item's data was last fetched, and was new or changed.", null=True, blank=True)),
                ('latitude', models.DecimalField(null=True, max_digits=12, decimal_places=9, blank=True)),
                ('longitude', models.DecimalField(null=True, max_digits=12, decimal_places=9, blank=True)),
                ('raw', models.TextField(help_text=b'eg, the raw JSON from the API.', blank=True)),
                ('text', models.CharField(max_length=255)),
                ('twitter_id', models.BigIntegerField(unique=True)),
                ('twitter_id_str', models.CharField(unique=True, max_length=20)),
                ('created_at', models.DateTimeField(help_text=b'UTC time when this Tweet was created on Twitter')),
                ('favorite_count', models.PositiveIntegerField(help_text=b'Approximately how many times this has been favorited')),
                ('retweet_count', models.PositiveIntegerField(help_text=b'Number of times this has been retweeted')),
                ('in_reply_to_screen_name', models.CharField(help_text=b"Screen name of the original Tweet's author, if this is a reply", max_length=20, blank=True)),
                ('in_reply_to_status_id', models.BigIntegerField(help_text=b'The ID of the Tweet replied to, if any', null=True, blank=True)),
                ('in_reply_to_status_id_str', models.CharField(max_length=20, blank=True)),
                ('in_reply_to_user_id', models.BigIntegerField(help_text=b"ID of the original Tweet's author, if this is a reply", null=True, blank=True)),
                ('in_reply_to_user_id_str', models.CharField(max_length=20, blank=True)),
                ('language', models.CharField(default=b'und', help_text=b"A BCP 47 language identifier, or 'und' if it couldn't be detected", max_length=20)),
                ('place_attribute_street_address', models.CharField(max_length=255, blank=True)),
                ('place_full_name', models.CharField(max_length=255, blank=True)),
                ('place_country', models.CharField(max_length=255, blank=True)),
                ('quoted_status_id', models.BigIntegerField(help_text=b'The ID of the Tweet quoted, if any', null=True, blank=True)),
                ('quoted_status_id_str', models.CharField(max_length=20, blank=True)),
                ('source', models.CharField(help_text=b'Utility used to post the Tweet', max_length=255, blank=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
            bases=(ditto.core.models.DiffModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_created', models.DateTimeField(help_text=b'The time this item was created in the database.', auto_now_add=True)),
                ('time_modified', models.DateTimeField(help_text=b'The time this item was last saved to the database.', auto_now=True)),
                ('twitter_id', models.BigIntegerField(unique=True)),
                ('twitter_id_str', models.CharField(unique=True, max_length=20)),
                ('screen_name', models.CharField(help_text=b"Username, eg, 'samuelpepys'", max_length=20)),
                ('name', models.CharField(help_text=b"eg, 'Samuel Pepys'", max_length=30)),
                ('url', models.URLField(help_text=b'A URL provided by the user as part of their profile', blank=True)),
                ('is_private', models.BooleanField(default=False, help_text=b"True if this user is 'protected' or private")),
                ('is_verified', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(help_text=b'UTC time when this account was created on Twitter')),
                ('description', models.CharField(max_length=255, blank=True)),
                ('location', models.CharField(max_length=255, blank=True)),
                ('time_zone', models.CharField(max_length=255, blank=True)),
                ('profile_image_url', models.URLField(max_length=255, blank=True)),
                ('profile_image_url_https', models.URLField(max_length=255, blank=True)),
                ('favorites_count', models.PositiveIntegerField(help_text=b'The number of tweets this user has favorited in the account\xe2\x80\x99s lifetime')),
                ('followers_count', models.PositiveIntegerField(help_text=b'The number of followers this account has')),
                ('friends_count', models.PositiveIntegerField(help_text=b'Tne number of users this account is following.')),
                ('listed_count', models.PositiveIntegerField(help_text=b'The number of public lists this user is a member of')),
                ('statuses_count', models.PositiveIntegerField(help_text=b'The number of tweets, including retweets, by this user')),
                ('fetch_time', models.DateTimeField(help_text=b'The time the data was last fetched, and was new or changed.', null=True, blank=True)),
                ('raw', models.TextField(help_text=b'eg, the raw JSON from the API.', blank=True)),
            ],
            options={
                'ordering': ['screen_name'],
            },
            bases=(ditto.core.models.DiffModelMixin, models.Model),
        ),
        migrations.AlterField(
            model_name='account',
            name='screen_name',
            field=models.CharField(help_text=b"Username, eg, 'samuelpepys'", unique=True, max_length=20, blank=True),
        ),
        migrations.AddField(
            model_name='tweet',
            name='user',
            field=models.ForeignKey(to='twitter.User'),
        ),
        migrations.AddField(
            model_name='account',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='twitter.User', null=True),
        ),
    ]
