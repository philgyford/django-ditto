# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0003_auto_20150626_1558"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookmark",
            name="url",
            field=models.TextField(validators=[django.core.validators.URLValidator()]),
        ),
    ]
