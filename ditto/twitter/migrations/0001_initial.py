# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_created', models.DateTimeField(help_text=b'The time this item was created in the database.', auto_now_add=True)),
                ('time_modified', models.DateTimeField(help_text=b'The time this item was last saved to the database.', auto_now=True)),
                ('screen_name', models.CharField(max_length=20, blank=True)),
                ('consumer_key', models.CharField(max_length=255, blank=True)),
                ('consumer_secret', models.CharField(max_length=255, blank=True)),
                ('access_token', models.CharField(max_length=255, blank=True)),
                ('access_token_secret', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'ordering': ['screen_name'],
            },
        ),
    ]
