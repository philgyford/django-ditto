from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0008_bookmark_tags"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookmark",
            name="post_time",
            field=models.DateTimeField(
                help_text=b"The time this was created on Pinboard.",
                null=True,
                blank=True,
            ),
        ),
    ]
