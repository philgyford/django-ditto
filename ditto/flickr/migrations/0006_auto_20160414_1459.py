# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("flickr", "0005_auto_20160414_1427"),
    ]

    operations = [
        migrations.RenameField(
            model_name="photo",
            old_name="large_2400_height",
            new_name="large_2048_height",
        ),
        migrations.RenameField(
            model_name="photo",
            old_name="large_2400_width",
            new_name="large_2048_width",
        ),
    ]
