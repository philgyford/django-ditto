from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0009_auto_20150729_1056"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookmark",
            name="latitude",
            field=models.DecimalField(
                null=True, max_digits=12, decimal_places=9, blank=True
            ),
        ),
        migrations.AddField(
            model_name="bookmark",
            name="longitude",
            field=models.DecimalField(
                null=True, max_digits=12, decimal_places=9, blank=True
            ),
        ),
    ]
