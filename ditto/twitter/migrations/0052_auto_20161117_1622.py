# Generated by Django 1.10.1 on 2016-11-17 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0051_auto_20160713_1444"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tweet",
            name="post_time",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                help_text="The time the item was originally posted/created on its service.",  # noqa: E501
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="tweet",
            name="summary",
            field=models.CharField(
                blank=True,
                help_text="eg, Brief summary or excerpt of item's text content. No linebreaks or HTML.",  # noqa: E501
                max_length=255,
            ),
        ),
    ]
