from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pinboard", "0004_auto_20150626_1603"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookmark",
            name="summary",
            field=models.CharField(
                help_text=b"eg, Initial text of a blog post, start of the description of a photo, all of a Tweet's text, etc.",  # noqa: E501
                max_length=255,
                blank=True,
            ),
        ),
    ]
