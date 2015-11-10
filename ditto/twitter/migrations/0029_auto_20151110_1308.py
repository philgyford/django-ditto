# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0028_auto_20151110_1139'),
    ]

    # Manually re-jigged to avoid losing any data:
    operations = [
        migrations.AlterField(
            model_name='tweet',
            name='created_at',
            field=models.DateTimeField(help_text='The time the item was originally posted/created on its service.', blank=True, null=True),
        ),
        migrations.RenameField(
            model_name='tweet',
            old_name='created_at',
            new_name='post_time',
        ),
        migrations.AlterModelOptions(
            name='tweet',
            options={'ordering': ['-post_time']},
        ),
    ]
