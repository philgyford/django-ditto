# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0026_auto_20151110_1131"),
    ]

    operations = [
        migrations.RemoveField(model_name="user", name="profile_image_url",),
    ]
