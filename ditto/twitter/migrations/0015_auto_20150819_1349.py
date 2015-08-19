# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0014_auto_20150819_1342'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tweet',
            name='favorite_count',
            field=models.PositiveIntegerField(help_text=b'Approximately how many times this had been favorited when fetched', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='retweet_count',
            field=models.PositiveIntegerField(help_text=b'Number of times this had been retweeted when fetched', null=True, blank=True),
        ),
    ]
