# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0019_auto_20151028_1556"),
    ]

    operations = [
        migrations.RenameField(
            model_name="photo", old_name="media_url", new_name="url",
        ),
        migrations.RemoveField(model_name="photo", name="page_url",),
    ]
