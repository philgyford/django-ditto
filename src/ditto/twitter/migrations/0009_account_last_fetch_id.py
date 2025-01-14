from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0008_remove_user_twitter_id_str"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="last_fetch_id",
            field=models.BigIntegerField(
                help_text=b"The Twitter ID of the most recent Tweet fetched.",
                null=True,
                blank=True,
            ),
        ),
    ]
