# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("flickr", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="photo",
            name="exif_iso",
            field=models.IntegerField(null=True, help_text="eg, '100'.", blank=True),
        ),
    ]
