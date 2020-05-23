# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0021_video"),
    ]

    operations = [
        migrations.RemoveField(model_name="photo", name="tweet",),
        migrations.RemoveField(model_name="video", name="tweet",),
        migrations.RemoveField(model_name="tweet", name="photos_count",),
        migrations.AddField(
            model_name="tweet",
            name="media_count",
            field=models.PositiveSmallIntegerField(
                default=0,
                blank=True,
                help_text="Number of Photos/Videos attached to this Tweet",
            ),
        ),
        migrations.DeleteModel(name="Photo",),
        migrations.DeleteModel(name="Video",),
    ]
