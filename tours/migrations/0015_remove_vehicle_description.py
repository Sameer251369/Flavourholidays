from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tours", "0014_vehicle_route_description"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="vehicle",
            name="description",
        ),
    ]
