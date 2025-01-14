from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0025_auto_20151109_1651"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="created_at",
            field=models.DateTimeField(
                help_text="UTC time when this account was created on Twitter",
                blank=True,
                null=True,
            ),
        ),
    ]
