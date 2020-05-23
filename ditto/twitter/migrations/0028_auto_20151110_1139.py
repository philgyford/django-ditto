# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0027_remove_user_profile_image_url"),
    ]

    operations = [
        migrations.RenameField(
            model_name="user", old_name="favorites_count", new_name="favourites_count",
        ),
    ]
