# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0017_account_is_active"),
    ]

    operations = [
        migrations.AddField(
            model_name="tweet",
            name="text_html",
            field=models.TextField(
                blank=True, help_text="An HTMLified version of the Tweet's text"
            ),
        ),
    ]
