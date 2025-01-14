from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0012_auto_20150814_1730"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="favorites",
            field=models.ManyToManyField(
                related_name="favoriting_users", to="twitter.Tweet"
            ),
        ),
    ]
