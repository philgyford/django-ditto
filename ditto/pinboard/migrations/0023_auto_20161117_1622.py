# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-17 16:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pinboard', '0022_auto_20160428_1542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmark',
            name='post_time',
            field=models.DateTimeField(blank=True, db_index=True, help_text='The time the item was originally posted/created on its service.', null=True),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='summary',
            field=models.CharField(blank=True, help_text="eg, Brief summary or excerpt of item's text content. No linebreaks or HTML.", max_length=255),
        ),
    ]