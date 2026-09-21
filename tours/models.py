from django.db import models

class Destination(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    cover_image_file = models.ImageField(upload_to='destinations/', blank=True, null=True)
    cover_image_url = models.URLField(blank=True, default='')
    altitude_range = models.CharField(max_length=100, blank=True)
    best_time = models.CharField(max_length=100, blank=True)

    @property
    def cover_image(self):
        if self.cover_image_file:
            return self.cover_image_file.url
        return self.cover_image_url

    def __str__(self):
        return self.name

class Tour(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='tours')
    tagline = models.CharField(max_length=255, default="Main Character Energy in the Himalayas ⚡")
    vibe_tag = models.CharField(max_length=100, default="#SnowVibes") # #SnowVibes, #OffbeatGenZ, #ThrillSeeker, #HoneymoonGlow
    duration_days = models.IntegerField(default=5)
    duration_nights = models.IntegerField(default=4)
    starting_price = models.IntegerField(default=15999) # INR
    difficulty = models.CharField(max_length=50, default="Moderate") # Chill, Moderate, Extreme
    cover_image_file = models.ImageField(upload_to='tours/', blank=True, null=True)
    cover_image_url = models.URLField(blank=True, default='')
    gallery_urls = models.JSONField(default=list, blank=True)
    overview = models.TextField()
    inclusions = models.JSONField(default=list, blank=True)
    exclusions = models.JSONField(default=list, blank=True)
    is_featured = models.BooleanField(default=True)

    @property
    def cover_image(self):
        if self.cover_image_file:
            return self.cover_image_file.url
        return self.cover_image_url

    def __str__(self):
        return f"{self.title} ({self.destination.name})"

class TourCheckpoint(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='checkpoints')
    day_number = models.IntegerField()
    title = models.CharField(max_length=200)
    location_name = models.CharField(max_length=150)
    altitude = models.CharField(max_length=50, blank=True) # e.g. "11,672 ft"
    description = models.TextField()
    insta_spot = models.CharField(max_length=250, blank=True) # "Floating Post Office Selfie Spot"
    vibe_highlight = models.CharField(max_length=250, blank=True) # "Sunset Kahwa by the lake"
    image_file = models.ImageField(upload_to='checkpoints/', blank=True, null=True)
    image_url = models.URLField(blank=True, default='')
    activities = models.JSONField(default=list, blank=True)

    @property
    def display_image_url(self):
        if self.image_file:
            return self.image_file.url
        return self.image_url

    class Meta:
        ordering = ['day_number']

    def __str__(self):
        return f"Day {self.day_number}: {self.title} - {self.tour.title}"

class BlogPost(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=100, default="Guide")
    read_time = models.CharField(max_length=50, default="4 min read")
    author = models.CharField(max_length=100, default="Flavour Squad")
    cover_image_file = models.ImageField(upload_to='blogs/', blank=True, null=True)
    cover_image_url = models.URLField(blank=True, default='')
    excerpt = models.TextField()
    content = models.TextField()
    vibe_tag = models.CharField(max_length=100, default="#TravelHacks")
    related_tour = models.ForeignKey(Tour, on_delete=models.SET_NULL, null=True, blank=True, related_name='blogs')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def cover_image(self):
        if self.cover_image_file:
            return self.cover_image_file.url
        return self.cover_image_url

    def __str__(self):
        return self.title

class Vehicle(models.Model):
    name = models.CharField(max_length=150)
    model_name = models.CharField(max_length=150)
    capacity_passengers = models.CharField(max_length=100)
    terrain_type = models.CharField(max_length=150)
    description = models.TextField()
    image_file = models.ImageField(upload_to='vehicles/', blank=True, null=True)
    image_url = models.URLField(blank=True, default='')
    badge = models.CharField(max_length=100, default="4x4 Beast")

    @property
    def display_image_url(self):
        if self.image_file:
            return self.image_file.url
        return self.image_url

    def __str__(self):
        return self.name

class Inquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    travel_dates = models.CharField(max_length=100, blank=True)
    travelers_count = models.IntegerField(default=2)
    selected_tour = models.ForeignKey(Tour, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle_preference = models.CharField(max_length=100, blank=True)
    custom_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inquiry from {self.name} ({self.phone})"

class BookingSearch(models.Model):
    selected_tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='booking_searches')
    check_in = models.DateField()
    check_out = models.DateField()
    people = models.PositiveIntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.selected_tour.title} ({self.check_in} to {self.check_out})"

class Testimonial(models.Model):
    client_name = models.CharField(max_length=100)
    trip_type = models.CharField(max_length=100) # Honeymoon / Group Adventure
    rating = models.IntegerField(default=5)
    comment = models.TextField()
    avatar_file = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    avatar_url = models.URLField(blank=True, default='')
    location_visited = models.CharField(max_length=100, default="Kashmir")

    @property
    def display_avatar_url(self):
        if self.avatar_file:
            return self.avatar_file.url
        return self.avatar_url

    def __str__(self):
        return f"{self.client_name} - {self.rating} stars"

class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=100, default="General")

    def __str__(self):
        return self.question

