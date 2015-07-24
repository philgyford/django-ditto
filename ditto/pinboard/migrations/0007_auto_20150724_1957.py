# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pinboard', '0006_auto_20150723_1322'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='account',
            options={'ordering': ['username']},
        ),
        migrations.AlterModelOptions(
            name='bookmark',
            options={'ordering': ['-post_time']},
        ),
        migrations.AlterField(
            model_name='account',
            name='time_created',
            field=models.DateTimeField(help_text=b'The time this item was created in the database.', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='time_modified',
            field=models.DateTimeField(help_text=b'The time this item was last saved to the database.', auto_now=True),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='fetch_time',
            field=models.DateTimeField(help_text=b"The time the item's data was last fetched, and was new or changed.", null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='is_private',
            field=models.BooleanField(default=False, help_text=b'If set, this item will not be shown on public-facing pages.'),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='time_created',
            field=models.DateTimeField(help_text=b'The time this item was created in the database.', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='time_modified',
            field=models.DateTimeField(help_text=b'The time this item was last saved to the database.', auto_now=True),
        ),
    ]
