from django.db import migrations


RETURN_IMAGE = "https://images.pexels.com/photos/31029367/pexels-photo-31029367.jpeg?auto=compress&cs=tinysrgb&w=1200"


def add_return_checkpoint(apps, schema_editor):
    Tour = apps.get_model("tours", "Tour")
    TourCheckpoint = apps.get_model("tours", "TourCheckpoint")
    db = schema_editor.connection.alias
    tour = Tour.objects.using(db).filter(slug__startswith="kargil-suru-valley-expedition").first()

    if not tour:
        return

    TourCheckpoint.objects.using(db).get_or_create(
        tour_id=tour.pk,
        day_number=5,
        defaults={
            "title": "Kargil to Srinagar via Drass",
            "location_name": "Kargil, Drass & Sonamarg",
            "altitude": "11,575 ft at Zoji La",
            "description": "Retrace the mountain road through Drass and Sonamarg to Srinagar, with comfort stops and timing adjusted to current road conditions.",
            "insta_spot": "Last mountain views on the Kargil–Srinagar road",
            "vibe_highlight": "A scenic return through the valleys that connect Ladakh and Kashmir",
            "image_url": RETURN_IMAGE,
            "activities": ["Early departure", "Drass tea stop", "Sonamarg rest stop", "Srinagar drop-off"],
        },
    )


def reverse_checkpoint(apps, schema_editor):
    Tour = apps.get_model("tours", "Tour")
    TourCheckpoint = apps.get_model("tours", "TourCheckpoint")
    db = schema_editor.connection.alias
    tour = Tour.objects.using(db).filter(slug__startswith="kargil-suru-valley-expedition").first()
    if tour:
        TourCheckpoint.objects.using(db).filter(tour_id=tour.pk, day_number=5).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tours", "0004_replace_gurez_with_kargil"),
    ]

    operations = [
        migrations.RunPython(add_return_checkpoint, reverse_checkpoint),
    ]
