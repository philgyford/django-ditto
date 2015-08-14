# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0010_remove_tweet_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='tweet',
            name='text',
            field=models.TextField(default='', max_length=140),
            preserve_default=False,
        ),
    ]
