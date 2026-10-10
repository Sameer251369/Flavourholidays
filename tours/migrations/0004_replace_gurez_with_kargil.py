from django.db import migrations


KARGIL_COVER = "https://images.pexels.com/photos/31029367/pexels-photo-31029367.jpeg?auto=compress&cs=tinysrgb&w=1600"
KARGIL_DAY_TWO = "https://images.pexels.com/photos/33965719/pexels-photo-33965719.jpeg?auto=compress&cs=tinysrgb&w=1200"
KARGIL_DAY_THREE = "https://images.pexels.com/photos/37835745/pexels-photo-37835745.jpeg?auto=compress&cs=tinysrgb&w=1200"
KARGIL_DAY_FOUR = "https://images.pexels.com/photos/31029368/pexels-photo-31029368.jpeg?auto=compress&cs=tinysrgb&w=1200"


def replace_gurez_with_kargil(apps, schema_editor):
    Destination = apps.get_model("tours", "Destination")
    Tour = apps.get_model("tours", "Tour")
    TourCheckpoint = apps.get_model("tours", "TourCheckpoint")
    BlogPost = apps.get_model("tours", "BlogPost")
    FAQ = apps.get_model("tours", "FAQ")
    Vehicle = apps.get_model("tours", "Vehicle")
    Testimonial = apps.get_model("tours", "Testimonial")

    db = schema_editor.connection.alias
    old_tour = Tour.objects.using(db).filter(slug="offbeat-gurez-valley-frontier").first()
    old_destination = Destination.objects.using(db).filter(slug="gurez-frontier").first()

    kargil_destination = Destination.objects.using(db).filter(slug="kargil").first()
    if not kargil_destination:
        kargil_destination = Destination.objects.using(db).create(
            name="Kargil",
            slug="kargil",
            description="A high-mountain gateway between Kashmir and Leh, with the Drass valley, Kargil town, and the Suru River route.",
            cover_image_url=KARGIL_COVER,
            altitude_range="8,780 ft - 11,575 ft (Zoji La)",
            best_time="May - October, subject to road access",
        )

    if old_tour:
        old_tour.title = "Kargil & Suru Valley Mountain Expedition"
        new_tour_slug = "kargil-suru-valley-expedition"
        if Tour.objects.using(db).exclude(pk=old_tour.pk).filter(slug=new_tour_slug).exists():
            new_tour_slug = f"{new_tour_slug}-{old_tour.pk}"
        old_tour.slug = new_tour_slug
        old_tour.destination = kargil_destination
        old_tour.tagline = "High mountain passes, Suru Valley rivers & stories from the Himalayas 🏔️"
        old_tour.vibe_tag = "#OffbeatGenZ"
        old_tour.duration_days = 5
        old_tour.duration_nights = 4
        old_tour.starting_price = 19999
        old_tour.difficulty = "Moderate"
        old_tour.cover_image_url = KARGIL_COVER
        old_tour.gallery_urls = [KARGIL_COVER, KARGIL_DAY_TWO, KARGIL_DAY_THREE]
        old_tour.overview = "Travel from Srinagar to Kargil through the mountain landscapes of Sonamarg and Drass, then explore the Suru Valley and the region's layered history with a locally planned route."
        old_tour.inclusions = [
            "Private 4WD transfer for mountain roads",
            "Four nights of comfortable stays along the route",
            "Kargil War Memorial visit in Drass",
            "Guided Suru Valley and Sankoo day excursion",
            "Local host support and route planning",
        ]
        old_tour.exclusions = [
            "Airfare or train tickets to Srinagar",
            "Meals not listed in the final itinerary",
            "Personal expenses and travel insurance",
        ]
        old_tour.is_featured = True
        old_tour.save(using=db)

        checkpoint_updates = {
            1: {
                "title": "Srinagar to Kargil via Sonamarg & Drass",
                "location_name": "Zoji La, Drass & Kargil",
                "altitude": "11,575 ft at Zoji La",
                "description": "Set out from Srinagar through Sonamarg and cross the Zoji La route to Drass before continuing to Kargil. Stops are planned around road and weather conditions.",
                "insta_spot": "Mountain views from the Zoji La road",
                "vibe_highlight": "A full-day Himalayan drive from Kashmir into Kargil",
                "image_url": KARGIL_COVER,
                "activities": ["Sonamarg stop", "Zoji La crossing (when open)", "Drass viewpoint", "Kargil check-in"],
            },
            2: {
                "title": "Drass Valley & Kargil War Memorial",
                "location_name": "Drass & Kargil",
                "altitude": "10,800 ft",
                "description": "Visit the Kargil War Memorial at Drass, then take time for the surrounding mountain viewpoints and local stories before returning to Kargil.",
                "insta_spot": "The memorial grounds with the mountains of Drass",
                "vibe_highlight": "A reflective day grounded in the history of the region",
                "image_url": KARGIL_DAY_TWO,
                "activities": ["Kargil War Memorial", "Drass town stop", "Mountain viewpoints", "Return to Kargil"],
            },
            3: {
                "title": "Suru Valley & Sankoo",
                "location_name": "Sankoo, Suru Valley",
                "altitude": "9,500 ft",
                "description": "Follow the Suru River south through green valley settlements and mountain scenery. Pause around Sankoo for a relaxed local visit before returning to Kargil.",
                "insta_spot": "Suru River framed by the valley peaks",
                "vibe_highlight": "A slower day among riverside villages and wide Himalayan views",
                "image_url": KARGIL_DAY_THREE,
                "activities": ["Suru River drive", "Sankoo village visit", "Local lunch stop", "Scenic return to Kargil"],
            },
            4: {
                "title": "Kargil Old Town & Local Life",
                "location_name": "Kargil town",
                "altitude": "8,780 ft",
                "description": "Spend an unhurried day exploring Kargil town, its market and nearby viewpoints. Your host can tailor the pace around local opening times and road conditions.",
                "insta_spot": "Evening light over the Kargil valley",
                "vibe_highlight": "Meet local makers and settle into the rhythm of town",
                "image_url": KARGIL_DAY_FOUR,
                "activities": ["Kargil bazaar walk", "Local food stop", "Nearby viewpoint", "Farewell dinner"],
            },
            5: {
                "title": "Kargil to Srinagar via Drass",
                "location_name": "Kargil, Drass & Sonamarg",
                "altitude": "11,575 ft at Zoji La",
                "description": "Retrace the mountain road through Drass and Sonamarg to Srinagar, with comfort stops and timing adjusted to current road conditions.",
                "insta_spot": "Last mountain views on the Kargil–Srinagar road",
                "vibe_highlight": "A scenic return through the valleys that connect Ladakh and Kashmir",
                "image_url": KARGIL_COVER,
                "activities": ["Early departure", "Drass tea stop", "Sonamarg rest stop", "Srinagar drop-off"],
            },
        }
        for day_number, fields in checkpoint_updates.items():
            TourCheckpoint.objects.using(db).filter(tour_id=old_tour.pk, day_number=day_number).update(**fields)
        TourCheckpoint.objects.using(db).filter(tour_id=old_tour.pk, day_number__gt=5).delete()

        old_slug_blog = BlogPost.objects.using(db).filter(slug="why-gurez-valley-is-ultimate-offbeat-destination-2026").first()
        if not old_slug_blog:
            old_slug_blog = BlogPost.objects.using(db).filter(related_tour_id=old_tour.pk).exclude(slug="kashmir-travel-rules-2026-sim-permits-snow-hacks").first()
        if old_slug_blog:
            old_slug_blog.title = "A First-Timer's Guide to Kargil & Suru Valley"
            new_blog_slug = "kargil-suru-valley-first-timer-guide"
            if BlogPost.objects.using(db).exclude(pk=old_slug_blog.pk).filter(slug=new_blog_slug).exists():
                new_blog_slug = f"{new_blog_slug}-{old_slug_blog.pk}"
            old_slug_blog.slug = new_blog_slug
            old_slug_blog.category = "Offbeat Gems"
            old_slug_blog.read_time = "5 min read"
            old_slug_blog.cover_image_url = KARGIL_COVER
            old_slug_blog.excerpt = "Plan a thoughtful Kargil stay with notes on the Drass memorial, Suru Valley, mountain-road timing and what to confirm locally."
            old_slug_blog.content = """Kargil sits on the mountain road between Kashmir and Leh, with the Suru River valley branching south from town. Build in time for the journey itself and keep the daily plan flexible around road and weather conditions.\n\n#### Ideas for your Kargil stay:\n- **Drass**: Visit the Kargil War Memorial and nearby viewpoints.\n- **Suru Valley**: Take a scenic drive toward Sankoo and the riverside settlements.\n- **Kargil town**: Leave space for the bazaar, local food and conversations with your host.\n\nCheck current Zoji La access and confirm any restrictions that apply to optional border-area stops before travel."""
            old_slug_blog.related_tour = old_tour
            old_slug_blog.save(using=db)

        BlogPost.objects.using(db).filter(related_tour_id=old_tour.pk).exclude(pk=getattr(old_slug_blog, "pk", None)).update(related_tour=None)

    if old_destination and not Tour.objects.using(db).filter(destination_id=old_destination.pk).exists():
        old_destination.delete(using=db)

    FAQ.objects.using(db).filter(question__icontains="Gurez").update(
        question="Do I need permits to visit Kargil and Suru Valley?",
        answer="Kargil is on the main Srinagar–Leh route, though some restricted or border-area stops may require advance permission. Our local team confirms requirements for your exact itinerary.",
        category="Permits & Access",
    )
    Vehicle.objects.using(db).filter(description__icontains="Gurez").update(
        terrain_type="Winter Snow & High Altitude Mountain Roads (Zoji La, Khardung La)",
        description="A capable 4WD for mountain routes between Tangmarg, Kargil and Ladakh, with local drivers familiar with changing road conditions.",
    )
    Testimonial.objects.using(db).filter(comment__icontains="Gurez").update(
        trip_type="Kargil & Suru Valley Expedition",
        comment="Kargil and the Suru Valley were unforgettable. The mountain drive and local stops arranged by Flavour Holidays made the whole trip feel effortless.",
        location_visited="Kargil & Suru Valley",
    )

    for blog in BlogPost.objects.using(db).filter(excerpt__icontains="Gurez"):
        blog.excerpt = "Planning a Kashmir trip? Here's what to know about staying connected, checking mountain-road conditions, and making time for Kargil's historic stops."
        blog.save(using=db, update_fields=["excerpt"])
    for blog in BlogPost.objects.using(db).filter(content__icontains="Gurez"):
        blog.content = blog.content.replace(
            "### 2. Inner Line Permits (Gurez & Bangus Valley)\nPlaces like Gurez Valley and Bangus Valley lie close to the Line of Control. While regular tourist spots like Gulmarg and Pahalgam need no permits, **Gurez requires an Inner Line Permit (ILP)**. Flavour Holidays processes all ILPs seamlessly for our guests!",
            "### 2. Check road access before you go\nMountain routes can change with weather and seasonal closures. Confirm Zoji La access and any requirements for restricted-area stops with your local host before departure.",
        )
        blog.save(using=db, update_fields=["content"])


def reverse_replacement(apps, schema_editor):
    # The conversion replaces tour content rather than archiving a second itinerary.
    # Keep reverse migration safe and non-destructive; restoring Gurez requires source data.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("tours", "0003_remove_blogpost_cover_image_and_more"),
    ]

    operations = [
        migrations.RunPython(replace_gurez_with_kargil, reverse_replacement),
    ]
