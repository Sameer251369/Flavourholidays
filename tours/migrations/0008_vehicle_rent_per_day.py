from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tours", "0007_blogpost_allow_indexing_blogpost_canonical_url_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicle",
            name="rent_per_day",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Daily rental rate in Indian rupees.",
                null=True,
                verbose_name="Rent per day (₹)",
            ),
        ),
    ]
