# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0008_bookmark_tags"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookmark",
            name="post_time",
            field=models.DateTimeField(
                help_text=b"The time this was created on Pinboard.",
                null=True,
                blank=True,
            ),
        ),
    ]
