# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pinboard', '0014_auto_20151028_1556'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmark',
            name='post_time',
            field=models.DateTimeField(help_text='The time the item was originally posted/created on its service.', blank=True, null=True),
        ),
    ]
