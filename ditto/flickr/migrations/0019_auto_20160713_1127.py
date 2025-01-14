# Generated by Django 1.9.5 on 2016-07-13 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flickr", "0018_auto_20160525_1011"),
    ]

    operations = [
        migrations.AlterField(
            model_name="photo",
            name="safety_level",
            field=models.PositiveSmallIntegerField(
                choices=[(0, "None"), (1, "Safe"), (2, "Moderate"), (3, "Restricted")],
                default=0,
            ),
        ),
    ]
