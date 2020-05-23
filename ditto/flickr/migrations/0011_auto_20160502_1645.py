# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-02 16:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        ("flickr", "0010_photo_photosets"),
    ]

    operations = [
        migrations.RemoveField(model_name="photo", name="photosets",),
        migrations.AddField(
            model_name="photoset",
            name="photos",
            field=sortedm2m.fields.SortedManyToManyField(
                help_text=None, related_name="photosets", to="flickr.Photo"
            ),
        ),
        migrations.AlterField(
            model_name="photoset",
            name="primary_photo",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="primary_photosets",
                to="flickr.Photo",
            ),
        ),
    ]
