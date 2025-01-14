from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0029_auto_20151110_1308"),
    ]

    operations = [
        migrations.AlterField(
            model_name="account",
            name="consumer_key",
            field=models.CharField(
                help_text="(API Key) From https://apps.twitter.com",
                blank=True,
                max_length=255,
            ),
        ),
    ]
