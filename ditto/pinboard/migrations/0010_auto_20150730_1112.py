# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0009_auto_20150729_1056"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookmark",
            name="latitude",
            field=models.DecimalField(
                null=True, max_digits=12, decimal_places=9, blank=True
            ),
        ),
        migrations.AddField(
            model_name="bookmark",
            name="longitude",
            field=models.DecimalField(
                null=True, max_digits=12, decimal_places=9, blank=True
            ),
        ),
    ]
