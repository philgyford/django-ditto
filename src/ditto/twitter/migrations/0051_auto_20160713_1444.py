# Generated by Django 1.9.5 on 2016-07-13 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0050_auto_20160713_1400"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="url",
            field=models.URLField(
                blank=True,
                default="",
                help_text="A URL provided by the user as part of their profile",
                max_length=255,
            ),
        ),
    ]
