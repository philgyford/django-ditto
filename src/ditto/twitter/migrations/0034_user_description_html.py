from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0033_auto_20160421_1602"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="description_html",
            field=models.TextField(
                help_text="An HTMLified version of the User's description", blank=True
            ),
        ),
    ]
