# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0005_auto_20150626_1702"),
    ]

    operations = [
        migrations.AlterField(
            model_name="account",
            name="url",
            field=models.URLField(
                help_text=b"eg, 'https://pinboard.in/u:philgyford'",
                unique=True,
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="bookmark",
            name="summary",
            field=models.CharField(
                help_text=b"eg, Initial text of a blog post, start of the description of a photo, all of a Tweet's text, etc. No HTML.",  # noqa: E501
                max_length=255,
                blank=True,
            ),
        ),
    ]
