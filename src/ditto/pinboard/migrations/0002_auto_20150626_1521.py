from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="bookmark",
            name="shared",
        ),
        migrations.AlterField(
            model_name="bookmark",
            name="raw",
            field=models.TextField(
                help_text=b"eg, the raw JSON from the API.", blank=True
            ),
        ),
    ]
