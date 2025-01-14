from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0016_auto_20151119_1702"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookmark",
            name="fetch_time",
            field=models.DateTimeField(
                blank=True,
                help_text="The time the item's data was last fetched.",
                null=True,
            ),
        ),
    ]
