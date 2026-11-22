from django.db import migrations
from django.utils.text import slugify


DESTINATIONS = {
    'kashmir': [
        ('Srinagar', 'Dal Lake, houseboats and heritage gardens.', 'https://images.unsplash.com/photo-1595815771614-ade9d652a65d?q=80&w=1200&auto=format&fit=crop'),
        ('Gulmarg', 'Alpine meadows, winter snow and the famous gondola.', 'https://images.unsplash.com/photo-1548625149-fc4a29cf7092?q=80&w=1200&auto=format&fit=crop'),
        ('Pahalgam', 'Riverside walks, pine forests and open mountain valleys.', 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=1200&auto=format&fit=crop'),
        ('Sonamarg', 'Glacier views and dramatic high mountain scenery.', 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1200&auto=format&fit=crop'),
        ('Gurez Valley', 'A quiet high valley of rivers, villages and wide peaks.', 'https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=1200&auto=format&fit=crop'),
        ('Doodhpathri', 'Rolling green meadows and clear mountain streams.', 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=1200&auto=format&fit=crop'),
        ('Yusmarg', 'Forest trails and peaceful meadows in the Pir Panjal.', 'https://images.unsplash.com/photo-1470770841072-f978cf4d019e?q=80&w=1200&auto=format&fit=crop'),
    ],
    'ladakh': [
        ('Leh', 'A high-altitude base for monasteries, markets and mountain routes.', 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?q=80&w=1200&auto=format&fit=crop'),
        ('Nubra Valley', 'Cold desert dunes, orchards and mountain villages.', 'https://images.unsplash.com/photo-1500534623283-312aade485b7?q=80&w=1200&auto=format&fit=crop'),
        ('Pangong Lake', 'A high-altitude lake known for changing shades of blue.', 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=1200&auto=format&fit=crop'),
        ('Tso Moriri', 'A remote lake and wildlife-rich Changthang landscape.', 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1200&auto=format&fit=crop'),
        ('Kargil', 'Mountain history, river valleys and a gateway between regions.', 'https://images.pexels.com/photos/31029367/pexels-photo-31029367.jpeg?auto=compress&cs=tinysrgb&w=1600'),
        ('Zanskar', 'Remote Himalayan villages, deep gorges and trekking routes.', 'https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=1200&auto=format&fit=crop'),
    ],
}

STAYS = ['Budget hotels', '3-star hotels', '4-star hotels', '5-star hotels', 'Luxury resorts', 'Houseboats', 'Camps and cottages']
TRANSPORTS = ['Sedan', 'SUV', 'Innova / Crysta', 'Tempo Traveller', 'Private transportation', 'Shared transportation']
ACTIVITIES = ['Shikara rides', 'Gondola rides', 'Skiing', 'Snow activities', 'Trekking', 'Camping', 'River rafting', 'ATV rides', 'Sightseeing', 'Photography experiences', 'Local cultural experiences']
BUDGETS = [
    ('Below ₹10,000', 0, 10000), ('₹10,000–₹20,000', 10000, 20000),
    ('₹20,000–₹35,000', 20000, 35000), ('₹35,000–₹50,000', 35000, 50000),
    ('₹50,000–₹75,000', 50000, 75000), ('₹75,000+', 75000, None),
]
STYLES = ['Family vacation', 'Honeymoon', 'Friends trip', 'Solo adventure', 'Luxury vacation', 'Adventure expedition', 'Corporate trip', 'Group expedition']


def seed_options(apps, schema_editor):
    Place = apps.get_model('tours', 'PlannerPlace')
    Stay = apps.get_model('tours', 'PlannerStayOption')
    Transport = apps.get_model('tours', 'PlannerTransportOption')
    Activity = apps.get_model('tours', 'PlannerActivity')
    Budget = apps.get_model('tours', 'PlannerBudgetBand')
    Style = apps.get_model('tours', 'PlannerTravelStyle')
    for region, places in DESTINATIONS.items():
        for order, (name, description, image) in enumerate(places):
            Place.objects.get_or_create(slug=slugify(name), defaults={
                'name': name, 'region': region, 'description': description,
                'cover_image_url': image, 'is_active': True, 'sort_order': order,
            })
    for model, labels in ((Stay, STAYS), (Transport, TRANSPORTS), (Activity, ACTIVITIES)):
        for order, name in enumerate(labels):
            model.objects.get_or_create(slug=slugify(name), defaults={
                'name': name, 'is_active': True, 'sort_order': order,
                'description': '',
            })
    for order, (label, minimum, maximum) in enumerate(BUDGETS):
        Budget.objects.get_or_create(slug=f'budget-{order + 1}', defaults={
            'label': label, 'min_amount': minimum, 'max_amount': maximum,
            'is_active': True, 'sort_order': order,
        })
    for order, name in enumerate(STYLES):
        Style.objects.get_or_create(slug=slugify(name), defaults={
            'name': name, 'is_active': True, 'sort_order': order,
        })


class Migration(migrations.Migration):
    dependencies = [('tours', '0010_planneractivity_plannerbudgetband_plannerplace_and_more')]
    operations = [migrations.RunPython(seed_options, migrations.RunPython.noop)]
