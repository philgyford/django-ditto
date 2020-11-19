import json

from django.db import migrations


def backfill_photo_sizes(apps, schema_editor):
    """
    Go through all Photos and look at its raw Sizes JSON data, looking
    at the larger sizes that didn't originally exist.
    If a Photo has one of those sizes set in the JSON, but not set in
    its model fields, then set the width/height fields.

    This would have happened if the sizes existed in the Flickr API
    when we last fetched the Photo's data, but on that date we didn't
    yet have the corresponding model fields.

    This won't fetch new JSON data, so sizes added to the API since
    the data was last fetched for the photo won't be updated on the
    model fields.
    """
    Photo = apps.get_model("flickr", "Photo")

    # The sizes we'll backfill, if they exist in the JSON data we
    # already have.
    size_fields = (
        ("Medium 800", "medium_800"),
        ("Large", "large"),
        ("Large 1600", "large_1600"),
        ("Large 2048", "large_2048"),
        ("X-Large 3K", "x_large_3k"),
        ("X-Large 4K", "x_large_4k"),
        ("X-Large 5K", "x_large_5k"),
        ("X-Large 6K", "x_large_6k"),
    )

    for photo in Photo.objects.all():
        sizes_raw = json.loads(photo.sizes_raw)
        for size in sizes_raw["size"]:
            # size has keys "label", "width", "height"...
            for field in size_fields:
                width_field = "%s_width" % field[1]
                height_field = "%s_height" % field[1]
                if field[0] == size["label"] and getattr(photo, width_field) is None:
                    setattr(photo, width_field, size["width"])
                    setattr(photo, height_field, size["height"])
                    photo.save()


class Migration(migrations.Migration):

    dependencies = [
        ("flickr", "0024_auto_20201119_1539"),
    ]

    operations = [migrations.RunPython(backfill_photo_sizes)]
