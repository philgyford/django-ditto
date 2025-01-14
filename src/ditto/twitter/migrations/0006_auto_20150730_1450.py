from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("twitter", "0005_auto_20150730_1350"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="account",
            options={"ordering": ["-time_created"]},
        ),
        migrations.RemoveField(
            model_name="account",
            name="screen_name",
        ),
    ]
