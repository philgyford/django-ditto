import taggit.managers
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("taggit", "0001_initial"),
        ("pinboard", "0007_auto_20150724_1957"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookmark",
            name="tags",
            field=taggit.managers.TaggableManager(
                to="taggit.Tag",
                through="taggit.TaggedItem",
                help_text="A comma-separated list of tags.",
                verbose_name="Tags",
            ),
        ),
    ]
