# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0030_auto_20151119_1649"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tweet",
            name="fetch_time",
            field=models.DateTimeField(
                blank=True,
                help_text="The time the item's data was last fetched.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="fetch_time",
            field=models.DateTimeField(
                blank=True, help_text="The time the data was last fetched.", null=True
            ),
        ),
    ]
