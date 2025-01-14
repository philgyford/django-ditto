from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0002_auto_20150626_1521"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="bookmark",
            unique_together={("account", "url")},
        ),
    ]
