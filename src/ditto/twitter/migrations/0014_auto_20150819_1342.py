from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0013_user_favorites"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tweet",
            name="favorite_count",
            field=models.PositiveIntegerField(
                default=0,
                help_text=b"Approximately how many times this had been favorited when fetched",  # noqa: E501
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="tweet",
            name="retweet_count",
            field=models.PositiveIntegerField(
                default=0,
                help_text=b"Number of times this had been retweeted when fetched",
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="url",
            field=models.URLField(
                default=b"",
                help_text=b"A URL provided by the user as part of their profile",
                blank=True,
            ),
        ),
    ]
