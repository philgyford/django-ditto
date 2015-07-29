# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='consumer_key',
            field=models.CharField(help_text=b'(API Key)', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='consumer_secret',
            field=models.CharField(help_text=b'(API Secret)', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='screen_name',
            field=models.CharField(help_text=b"eg, 'philgyford'", unique=True, max_length=20, blank=True),
        ),
    ]
