# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0006_auto_20150730_1450'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tweet',
            name='in_reply_to_status_id_str',
        ),
        migrations.RemoveField(
            model_name='tweet',
            name='in_reply_to_user_id_str',
        ),
        migrations.RemoveField(
            model_name='tweet',
            name='quoted_status_id_str',
        ),
        migrations.RemoveField(
            model_name='tweet',
            name='twitter_id_str',
        ),
        migrations.AlterField(
            model_name='tweet',
            name='favorite_count',
            field=models.PositiveIntegerField(default=0, help_text=b'Approximately how many times this had been favorited when fetched'),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='retweet_count',
            field=models.PositiveIntegerField(default=0, help_text=b'Number of times this had been retweeted when fetched'),
        ),
    ]
