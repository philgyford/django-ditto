# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-14 15:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lastfm', '0002_auto_20160914_1314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='album',
            name='mbid',
            field=models.CharField(blank=True, db_index=True, help_text='MusicBrainz Identifier', max_length=36, verbose_name='MBID'),
        ),
        migrations.AlterField(
            model_name='artist',
            name='mbid',
            field=models.CharField(blank=True, db_index=True, help_text='MusicBrainz Identifier', max_length=36, verbose_name='MBID'),
        ),
        migrations.AlterField(
            model_name='track',
            name='mbid',
            field=models.CharField(blank=True, db_index=True, help_text='MusicBrainz Identifier', max_length=36, verbose_name='MBID'),
        ),
    ]