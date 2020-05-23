# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("flickr", "0006_auto_20160414_1459"),
    ]

    operations = [
        migrations.AlterField(
            model_name="photo",
            name="latitude",
            field=models.DecimalField(
                decimal_places=6, blank=True, null=True, max_digits=9
            ),
        ),
        migrations.AlterField(
            model_name="photo",
            name="longitude",
            field=models.DecimalField(
                decimal_places=6, blank=True, null=True, max_digits=9
            ),
        ),
    ]
