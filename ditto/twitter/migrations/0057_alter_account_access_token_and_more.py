# Generated by Django 4.0.2 on 2022-02-14 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0056_add_count_index"),
    ]

    operations = [
        migrations.AlterField(
            model_name="account",
            name="access_token",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Access Token"
            ),
        ),
        migrations.AlterField(
            model_name="account",
            name="access_token_secret",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Access Token Secret"
            ),
        ),
        migrations.AlterField(
            model_name="account",
            name="consumer_key",
            field=models.CharField(blank=True, max_length=255, verbose_name="API Key"),
        ),
        migrations.AlterField(
            model_name="account",
            name="consumer_secret",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="API Key Secret"
            ),
        ),
    ]
