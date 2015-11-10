# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0024_auto_20151104_1157'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='media',
            options={'verbose_name': 'Media item', 'ordering': ['time_created'], 'verbose_name_plural': 'Media items'},
        ),
        migrations.AlterField(
            model_name='tweet',
            name='twitter_id',
            field=models.BigIntegerField(db_index=True, unique=True),
        ),
    ]
