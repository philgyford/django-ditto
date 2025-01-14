from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0024_auto_20151104_1157"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="media",
            options={
                "verbose_name": "Media item",
                "ordering": ["time_created"],
                "verbose_name_plural": "Media items",
            },
        ),
        migrations.AlterField(
            model_name="tweet",
            name="twitter_id",
            field=models.BigIntegerField(db_index=True, unique=True),
        ),
    ]
