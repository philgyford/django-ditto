from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0007_auto_20150807_1432"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="twitter_id_str",
        ),
    ]
