# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0004_auto_20150730_1116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tweet',
            name='favorite_count',
            field=models.PositiveIntegerField(default=0, help_text=b'Approximately how many times this has been favorited'),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='retweet_count',
            field=models.PositiveIntegerField(default=0, help_text=b'Number of times this has been retweeted'),
        ),
    ]
