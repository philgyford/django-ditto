# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0003_auto_20150730_1112"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="favorites_count",
            field=models.PositiveIntegerField(
                default=0,
                help_text=b"The number of tweets this user has favorited in the account\xe2\x80\x99s lifetime",  # noqa: E501
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="followers_count",
            field=models.PositiveIntegerField(
                default=0, help_text=b"The number of followers this account has"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="friends_count",
            field=models.PositiveIntegerField(
                default=0, help_text=b"Tne number of users this account is following."
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="listed_count",
            field=models.PositiveIntegerField(
                default=0,
                help_text=b"The number of public lists this user is a member of",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="statuses_count",
            field=models.PositiveIntegerField(
                default=0,
                help_text=b"The number of tweets, including retweets, by this user",
            ),
        ),
    ]
