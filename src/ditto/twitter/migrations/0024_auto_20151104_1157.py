from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0023_media"),
    ]

    operations = [
        migrations.AddField(
            model_name="media",
            name="dash_url",
            field=models.URLField(null=True, verbose_name="MPEG-DASH URL", blank=True),
        ),
        migrations.AddField(
            model_name="media",
            name="webm_bitrate",
            field=models.PositiveIntegerField(
                null=True, verbose_name="WebM Bitrate", blank=True
            ),
        ),
        migrations.AddField(
            model_name="media",
            name="xmpeg_url",
            field=models.URLField(null=True, verbose_name="X-MPEG URL", blank=True),
        ),
    ]
