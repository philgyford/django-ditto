from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0015_auto_20151110_1308"),
    ]

    operations = [
        migrations.AlterField(
            model_name="account",
            name="api_token",
            field=models.CharField(
                verbose_name="API Token",
                max_length=51,
                help_text='eg, "philgyford:1234567890ABCDEFGHIJ"',
            ),
        ),
        migrations.AlterField(
            model_name="account",
            name="url",
            field=models.URLField(
                verbose_name="URL",
                unique=True,
                max_length=255,
                help_text="eg, 'https://pinboard.in/u:philgyford'",
            ),
        ),
    ]
