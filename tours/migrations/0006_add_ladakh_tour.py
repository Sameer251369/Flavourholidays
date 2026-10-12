from django.db import migrations


LADAKH_IMAGE = "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?q=80&w=1200&auto=format&fit=crop"

CHECKPOINTS = [
    {
        "day_number": 1,
        "title": "Leh Arrival & High Altitude Acclimatization",
        "location_name": "Leh Town",
        "altitude": "11,500 ft",
        "description": "Land at Kushok Bakula Rimpochee Airport (IXL). Complete rest mandatory for oxygen acclimatization. Evening leisurely walk in Leh Main Bazaar and Shanti Stupa sunset.",
        "insta_spot": "Shanti Stupa White Dome against Dusk Himalayan Range",
        "vibe_highlight": "First glimpse of Leh Palace lit up at night",
        "image_url": LADAKH_IMAGE,
        "activities": ["Airport Pickup", "Mandatory Hotel Rest", "Shanti Stupa Sunset", "Leh Market Walk"],
    },
    {
        "day_number": 2,
        "title": "Sham Valley: Magnetic Hill & Confluence of Indus & Zanskar",
        "location_name": "Sangam Point & Magnetic Hill",
        "altitude": "10,800 ft",
        "description": "Drive along the Leh-Srinagar highway. Experience the defying gravity at Magnetic Hill. Visit Gurudwara Pathar Sahib and witness the stunning confluence of emerald Zanskar and blue Indus rivers at Sangam.",
        "insta_spot": "Sangam Emerald & Blue River Confluence from High Lookout",
        "vibe_highlight": "White water river rafting in Zanskar River rapids",
        "image_url": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=800",
        "activities": ["Magnetic Hill Gravity Test", "Sangam River View", "Zanskar River Rafting Option", "Hall of Fame Visit"],
    },
    {
        "day_number": 3,
        "title": "Khardung La Pass (17,982 ft) to Nubra Valley Dunes",
        "location_name": "Khardung La & Hunder Sand Dunes",
        "altitude": "17,982 ft",
        "description": "Ascend the world's iconic Khardung La Pass (17,982ft). Take victory photos at the snow pass. Descend into Nubra Valley cold desert and ride double-humped Bactrian camels among silver sand dunes.",
        "insta_spot": "Khardung La World's Highest Pass Yellow Signboard",
        "vibe_highlight": "Riding double-humped Bactrian Camels in Hunder dunes under snow mountains",
        "image_url": LADAKH_IMAGE,
        "activities": ["Khardung La Crossing", "Diskit Monastery Giant Buddha", "Hunder Camel Safari", "Desert Camp Night"],
    },
    {
        "day_number": 4,
        "title": "Shyok River Route to Pangong Tso Lake",
        "location_name": "Pangong Tso (13,940 ft)",
        "altitude": "13,940 ft",
        "description": "Drive via the thrilling off-road Shyok riverbed route directly to Pangong Tso. Arrive at the 134km long lake that changes color from cyan to cobalt blue. Night camping in luxury geodesic domes.",
        "insta_spot": "Pangong Lake Turquoise Blue Horizon & 3 Idiots Yellow Scooter Spot",
        "vibe_highlight": "Astrophotography & Milky Way stargazing next to Pangong Tso shores",
        "image_url": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=800",
        "activities": ["Shyok River Off-roading", "Pangong Lake Check-in", "Sunset Lake Walk", "Stargazing Bonfire"],
    },
    {
        "day_number": 5,
        "title": "Chang La Pass (17,590 ft) & Return to Leh",
        "location_name": "Chang La Pass & Thiksey Monastery",
        "altitude": "17,590 ft",
        "description": "Sunrise photos at Pangong Lake. Return to Leh crossing Chang La Pass. Visit the magnificent 12-storey Thiksey Monastery (Mini Potala Palace) overlooking Indus Valley.",
        "insta_spot": "Thiksey Monastery Sunrise Tiered Architecture",
        "vibe_highlight": "Listening to morning Buddhist prayers and gong chimes at Thiksey",
        "image_url": LADAKH_IMAGE,
        "activities": ["Sunrise Pangong Shoot", "Chang La Pass Crossing", "Thiksey Monastery Visit", "Farewell Dinner in Leh"],
    },
]


def add_ladakh_tour(apps, schema_editor):
    Destination = apps.get_model("tours", "Destination")
    Tour = apps.get_model("tours", "Tour")
    TourCheckpoint = apps.get_model("tours", "TourCheckpoint")
    db = schema_editor.connection.alias

    destination, _ = Destination.objects.using(db).get_or_create(
        slug="leh-ladakh",
        defaults={
            "name": "Leh & Ladakh",
            "description": "High-altitude desert wonderland: Cold desert dunes, turquoise lakes, world's highest motorable passes, and ancient monasteries.",
            "cover_image_url": LADAKH_IMAGE,
            "altitude_range": "11,500 ft - 19,000 ft",
            "best_time": "May - September",
        },
    )

    tour, _ = Tour.objects.using(db).get_or_create(
        slug="leh-ladakh-high-altitude-thrill",
        defaults={
            "title": "Leh-Ladakh High Altitude Thrill Expedition",
            "destination_id": destination.pk,
            "tagline": "Khardung La, Pangong Tso Stargazing & Himalayan Bike/Thar Vibes 🔥",
            "vibe_tag": "#ThrillSeeker",
            "duration_days": 7,
            "duration_nights": 6,
            "starting_price": 24999,
            "difficulty": "Extreme",
            "cover_image_url": LADAKH_IMAGE,
            "gallery_urls": [
                LADAKH_IMAGE,
                "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=800",
            ],
            "overview": "The legendary 7-day high-altitude Ladakh circuit. Cross Khardung La (17,982 ft) into Nubra Valley's double-humped camel dunes, camp beside the color-changing Pangong Lake, and stargaze under Milky Way skies.",
            "inclusions": [
                "Leh Airport Pickup & Drop",
                "Oxygen Cylinder & Oxygen Level Monitors in all vehicles",
                "Ladakh Inner Line Permits & Environmental Fees",
                "Luxury Swiss Cottage Camps at Pangong Tso & Hunder Dunes",
                "Option for Royal Enfield Himalayan Bike Ride or 4x4 SUV",
            ],
            "exclusions": ["Monastery entrance tickets", "Bactrian Camel Ride fee"],
            "is_featured": True,
        },
    )

    for checkpoint in CHECKPOINTS:
        TourCheckpoint.objects.using(db).get_or_create(
            tour_id=tour.pk,
            day_number=checkpoint["day_number"],
            defaults=checkpoint,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tours", "0005_add_kargil_return_checkpoint"),
    ]

    operations = [
        migrations.RunPython(add_ladakh_tour, migrations.RunPython.noop),
    ]
