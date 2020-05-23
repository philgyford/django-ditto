# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-29 16:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flickr", "0008_auto_20160429_1559"),
    ]

    operations = [
        migrations.AddField(
            model_name="photoset",
            name="fetch_time",
            field=models.DateTimeField(
                blank=True,
                help_text="The time the item's data was last fetched.",
                null=True,
            ),
        ),
    ]
