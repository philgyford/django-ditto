from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flickr", "0002_auto_20160406_1548"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="photo",
            options={"ordering": ("-post_time",)},
        ),
        migrations.AlterField(
            model_name="photo",
            name="fetch_time",
            field=models.DateTimeField(
                blank=True,
                help_text="The time the item's data was last fetched.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="fetch_time",
            field=models.DateTimeField(
                blank=True, help_text="The time the data was last fetched.", null=True
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="iconserver",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
