from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0016_auto_20151002_1525"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="is_active",
            field=models.BooleanField(
                help_text="If false, new Tweets won't be fetched.", default=True
            ),
        ),
    ]
