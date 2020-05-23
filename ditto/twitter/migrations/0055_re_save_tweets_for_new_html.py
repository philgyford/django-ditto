# Generated by Django 2.0.4 on 2018-04-16 11:44

from django.db import migrations


def re_save_tweets(apps, schema_editor):
    """
    Re-save all of the Tweets so that the HTML version of their text is updated
    using the newer version of Twython.
    """
    Tweet = apps.get_model("twitter", "Tweet")

    for tweet in Tweet.objects.all():
        tweet.save(update_fields=["text_html"])


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0054_auto_20171113_1001"),
    ]

    operations = [
        migrations.RunPython(re_save_tweets),
    ]
