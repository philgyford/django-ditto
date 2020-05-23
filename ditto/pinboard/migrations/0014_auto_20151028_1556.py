# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0013_auto_20151026_1546"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="bookmarktag",
            options={"verbose_name_plural": "Tags", "verbose_name": "Tag"},
        ),
        migrations.AlterField(
            model_name="bookmark",
            name="is_private",
            field=models.BooleanField(
                default=False,
                help_text="If true, this item will not be shown on public-facing pages."
            ),
        ),
    ]
