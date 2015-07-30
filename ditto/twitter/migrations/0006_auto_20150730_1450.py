# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0005_auto_20150730_1350'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='account',
            options={'ordering': ['-time_created']},
        ),
        migrations.RemoveField(
            model_name='account',
            name='screen_name',
        ),
    ]
