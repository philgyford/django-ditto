# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0017_auto_20160413_0906"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookmark",
            name="latitude",
            field=models.DecimalField(
                decimal_places=6, blank=True, null=True, max_digits=9
            ),
        ),
        migrations.AlterField(
            model_name="bookmark",
            name="longitude",
            field=models.DecimalField(
                decimal_places=6, blank=True, null=True, max_digits=9
            ),
        ),
    ]
