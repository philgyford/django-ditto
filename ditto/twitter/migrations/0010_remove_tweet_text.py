# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0009_account_last_fetch_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tweet',
            name='text',
        ),
    ]
