from django.db import migrations, models


INITIAL_FARES = [
    ("Srinagar to Dal Lake", 1200, 1500, 2000),
    ("Srinagar to Tangmarg (Full Day Trip)", 2300, 3300, 6000),
    ("Srinagar to Gulmarg (Full Day Trip)", 2500, 3300, 6500),
    ("Srinagar to Yousmarg (Full Day Trip)", 2500, 3300, 6500),
    ("Srinagar to Sonamarg (Full Day Trip)", 2500, 3300, 6500),
    ("Srinagar to Pahalgam (Full Day Trip)", 2500, 3300, 6500),
    ("Srinagar to Mansbal Lake & Kheer Bawan", 2500, 3500, 6000),
    ("Srinagar to Wular Lake Round", 2800, 3500, 5500),
    ("Srinagar to Baltal (1 Day Trip)", 3000, 5000, 9000),
    ("Srinagar to Doodpathri", 2700, 3300, 6500),
    ("Srinagar to Naranag", 2500, 3300, 6000),
    ("Srinagar to Verinag (Full Day Trip)", 3500, 4000, 7500),
    ("Srinagar to Achabal & Kokernag (Full Day Trip)", 3500, 4200, 8000),
    ("Srinagar to Sinthan Top", 5000, 8000, 12000),
    ("Srinagar to Aharbal", 5000, 8500, 12000),
    ("Srinagar to Gurez Dawar", 18000, 20000, 29000),
]


def add_initial_fares(apps, schema_editor):
    Fare = apps.get_model("tours", "KashmirRouteFare")
    Fare.objects.using(schema_editor.connection.alias).bulk_create([
        Fare(
            destination=destination,
            sedan_price=sedan,
            innova_price=innova,
            tempo_traveller_price=tempo,
            sort_order=index,
        )
        for index, (destination, sedan, innova, tempo) in enumerate(INITIAL_FARES)
    ])


class Migration(migrations.Migration):
    dependencies = [("tours", "0012_planneradditionalservice_and_more")]

    operations = [
        migrations.CreateModel(
            name="KashmirRouteFare",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("destination", models.CharField(max_length=180, unique=True)),
                ("sedan_price", models.PositiveIntegerField(blank=True, help_text="Price in Indian rupees (₹). Leave blank to show ‘Ask for quote’.", null=True, verbose_name="Sedan (Etios/Swift Desire) (₹)")),
                ("innova_price", models.PositiveIntegerField(blank=True, help_text="Price in Indian rupees (₹). Leave blank to show ‘Ask for quote’.", null=True, verbose_name="Innova (₹)")),
                ("tempo_traveller_price", models.PositiveIntegerField(blank=True, help_text="Price in Indian rupees (₹). Leave blank to show ‘Ask for quote’.", null=True, verbose_name="Tempo Traveler (₹)")),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Kashmir taxi route fare",
                "verbose_name_plural": "Kashmir taxi route fares",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.RunPython(add_initial_fares, migrations.RunPython.noop),
    ]
