# Generated by Django 1.9.5 on 2016-05-05 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0035_auto_20160505_1137"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="media",
            name="mp4_bitrate_1",
        ),
        migrations.RemoveField(
            model_name="media",
            name="mp4_bitrate_2",
        ),
        migrations.RemoveField(
            model_name="media",
            name="mp4_bitrate_3",
        ),
        migrations.RemoveField(
            model_name="media",
            name="mp4_url_1",
        ),
        migrations.RemoveField(
            model_name="media",
            name="mp4_url_2",
        ),
        migrations.RemoveField(
            model_name="media",
            name="mp4_url_3",
        ),
        migrations.RemoveField(
            model_name="media",
            name="webm_bitrate",
        ),
        migrations.RemoveField(
            model_name="media",
            name="webm_url",
        ),
        migrations.AddField(
            model_name="media",
            name="mp4_url",
            field=models.URLField(
                blank=True, help_text="For Animated GIFs", verbose_name="MP4 URL"
            ),
        ),
    ]
