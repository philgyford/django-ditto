# Generated by Django 3.1.3 on 2020-11-19 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flickr", "0023_auto_20180104_1457"),
    ]

    operations = [
        migrations.AddField(
            model_name="photo",
            name="x_large_3k_height",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="photo",
            name="x_large_3k_width",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="photo",
            name="x_large_4k_height",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="photo",
            name="x_large_4k_width",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="photo",
            name="x_large_5k_height",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="photo",
            name="x_large_5k_width",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="photo",
            name="x_large_6k_height",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="photo",
            name="x_large_6k_width",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
