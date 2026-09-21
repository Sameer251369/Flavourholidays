from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('tours', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingSearch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('check_in', models.DateField()),
                ('check_out', models.DateField()),
                ('people', models.PositiveIntegerField(default=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('selected_tour', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_searches', to='tours.tour')),
            ],
        ),
    ]