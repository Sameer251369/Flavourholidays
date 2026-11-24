from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tours", "0013_kashmirroutefare"),
    ]

    def populate_route_descriptions(apps, schema_editor):
        Vehicle = apps.get_model("tours", "Vehicle")
        defaults = {
            "Mahindra Thar / Scorpio 4WD": "Srinagar, Tangmarg and Gulmarg, with onward winter routes to Kargil and Ladakh when roads are open.",
            "Toyota Innova Crysta": "Comfortable Srinagar airport transfers and longer journeys to Pahalgam, Sonamarg and Gulmarg.",
            "Tempo Traveller (12 / 17 / 26 Seater)": "Group transfers and multi-day itineraries between Srinagar, Gulmarg, Pahalgam, Kargil and Ladakh.",
        }
        for name, route in defaults.items():
            Vehicle.objects.filter(name=name, route_description="").update(route_description=route)

    operations = [
        migrations.AddField(
            model_name="vehicle",
            name="route_description",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Routes this vehicle is suited for, shown in the homepage fleet table.",
            ),
        ),
        migrations.RunPython(populate_route_descriptions, migrations.RunPython.noop),
    ]
