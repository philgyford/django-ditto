# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0015_auto_20150819_1349'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='account',
            options={'ordering': ['user__screen_name']},
        ),
        migrations.AlterField(
            model_name='account',
            name='consumer_key',
            field=models.CharField(help_text='(API Key)', blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='account',
            name='consumer_secret',
            field=models.CharField(help_text='(API Secret)', blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='account',
            name='last_favorite_id',
            field=models.BigIntegerField(help_text='The Twitter ID of the most recent favorited Tweet fetched.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='last_recent_id',
            field=models.BigIntegerField(help_text='The Twitter ID of the most recent Tweet fetched.', null=True, blank=True),
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
            model_name='tweet',
            name='created_at',
            field=models.DateTimeField(help_text='UTC time when this Tweet was created on Twitter'),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='favorite_count',
            field=models.PositiveIntegerField(help_text='Approximately how many times this had been favorited when fetched', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='fetch_time',
            field=models.DateTimeField(help_text="The time the item's data was last fetched, and was new or changed.", null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='in_reply_to_screen_name',
            field=models.CharField(help_text="Screen name of the original Tweet's author, if this is a reply", blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='in_reply_to_status_id',
            field=models.BigIntegerField(help_text='The ID of the Tweet replied to, if any', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='in_reply_to_user_id',
            field=models.BigIntegerField(help_text="ID of the original Tweet's author, if this is a reply", null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='is_private',
            field=models.BooleanField(help_text='If set, this item will not be shown on public-facing pages.', default=False),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='language',
            field=models.CharField(help_text="A BCP 47 language identifier, or 'und' if it couldn't be detected", default='und', max_length=20),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='permalink',
            field=models.URLField(help_text="URL of the item on the service's website.", blank=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='quoted_status_id',
            field=models.BigIntegerField(help_text='The ID of the Tweet quoted, if any', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='raw',
            field=models.TextField(help_text='eg, the raw JSON from the API.', blank=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='retweet_count',
            field=models.PositiveIntegerField(help_text='Number of times this had been retweeted when fetched', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='source',
            field=models.CharField(help_text='Utility used to post the Tweet', blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='summary',
            field=models.CharField(help_text="eg, Initial text of a blog post, start of the description of a photo, all of a Tweet's text, etc. No HTML.", blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='time_created',
            field=models.DateTimeField(help_text='The time this item was created in the database.', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='time_modified',
            field=models.DateTimeField(help_text='The time this item was last saved to the database.', auto_now=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='created_at',
            field=models.DateTimeField(help_text='UTC time when this account was created on Twitter'),
        ),
        migrations.AlterField(
            model_name='user',
            name='favorites_count',
            field=models.PositiveIntegerField(help_text='The number of tweets this user has favorited in the account’s lifetime', default=0),
        ),
        migrations.AlterField(
            model_name='user',
            name='fetch_time',
            field=models.DateTimeField(help_text='The time the data was last fetched, and was new or changed.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='followers_count',
            field=models.PositiveIntegerField(help_text='The number of followers this account has', default=0),
        ),
        migrations.AlterField(
            model_name='user',
            name='friends_count',
            field=models.PositiveIntegerField(help_text='Tne number of users this account is following.', default=0),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_private',
            field=models.BooleanField(help_text="True if this user is 'protected'", default=False),
        ),
        migrations.AlterField(
            model_name='user',
            name='listed_count',
            field=models.PositiveIntegerField(help_text='The number of public lists this user is a member of', default=0),
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(help_text="eg, 'Samuel Pepys'", max_length=30),
        ),
        migrations.AlterField(
            model_name='user',
            name='raw',
            field=models.TextField(help_text='eg, the raw JSON from the API.', blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='screen_name',
            field=models.CharField(help_text="Username, eg, 'samuelpepys'", max_length=20),
        ),
        migrations.AlterField(
            model_name='user',
            name='statuses_count',
            field=models.PositiveIntegerField(help_text='The number of tweets, including retweets, by this user', default=0),
        ),
        migrations.AlterField(
            model_name='user',
            name='time_created',
            field=models.DateTimeField(help_text='The time this item was created in the database.', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='time_modified',
            field=models.DateTimeField(help_text='The time this item was last saved to the database.', auto_now=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='url',
            field=models.URLField(help_text='A URL provided by the user as part of their profile', blank=True, default=''),
        ),
    ]
