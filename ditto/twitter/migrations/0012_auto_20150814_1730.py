# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0011_tweet_text'),
    ]

    operations = [
        migrations.RenameField(
            model_name='account',
            old_name='last_fetch_id',
            new_name='last_recent_id',
        ),
        migrations.AddField(
            model_name='account',
            name='last_favorite_id',
            field=models.BigIntegerField(help_text=b'The Twitter ID of the most recent favorited Tweet fetched.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_private',
            field=models.BooleanField(default=False, help_text=b"True if this user is 'protected'"),
        ),
    ]
