# Generated by Django 1.9.5 on 2016-05-25 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flickr", "0017_auto_20160524_1350"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="photos_url",
            field=models.URLField(max_length=255, verbose_name="Photos URL at Flickr"),
        ),
        migrations.AlterField(
            model_name="user",
            name="profile_url",
            field=models.URLField(max_length=255, verbose_name="Avatar URL on Flickr"),
        ),
    ]
