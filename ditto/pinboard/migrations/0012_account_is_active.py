# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0011_auto_20151002_1525"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="is_active",
            field=models.BooleanField(
                help_text="If false, new Bookmarks won't be fetched.", default=True
            ),
        ),
    ]
