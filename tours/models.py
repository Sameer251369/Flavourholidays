from django.db import models


class Destination(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    cover_image_file = models.ImageField(
        upload_to="destinations/",
        blank=True,
        null=True
    )
    cover_image_url = models.URLField(blank=True, default="")

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
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name="tours"
    )

    tagline = models.CharField(
        max_length=255,
        default="Main Character Energy in the Himalayas ⚡"
    )
    vibe_tag = models.CharField(
        max_length=100,
        default="#SnowVibes"
    )

    duration_days = models.IntegerField(default=5)
    duration_nights = models.IntegerField(default=4)
    starting_price = models.IntegerField(default=15999)
    difficulty = models.CharField(max_length=50, default="Moderate")

    cover_image_file = models.ImageField(
        upload_to="tours/",
        blank=True,
        null=True
    )
    cover_image_url = models.URLField(blank=True, default="")

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


class TourPricing(models.Model):
    class Audience(models.TextChoices):
        GROUP = "group", "Group"
        FAMILY = "family", "Family"
        COUPLE = "couple", "Couple"
        FRIENDS = "friends", "Friends"
        PER_PERSON = "per_person", "Per person"

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="pricing_options")
    audience = models.CharField(max_length=20, choices=Audience.choices)
    price = models.PositiveIntegerField(help_text="Price in Indian rupees (₹).")
    note = models.CharField(max_length=160, blank=True, help_text="Optional note shown with this price.")

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["tour", "audience"], name="unique_tour_audience_price")
        ]

    def __str__(self):
        return f"{self.tour.title} — {self.get_audience_display()}: ₹{self.price}"


class TourCheckpoint(models.Model):
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="checkpoints"
    )

    day_number = models.IntegerField()
    title = models.CharField(max_length=200)
    location_name = models.CharField(max_length=150)

    altitude = models.CharField(
        max_length=50,
        blank=True
    )

    description = models.TextField()

    insta_spot = models.CharField(
        max_length=250,
        blank=True
    )

    vibe_highlight = models.CharField(
        max_length=250,
        blank=True
    )

    image_file = models.ImageField(
        upload_to="checkpoints/",
        blank=True,
        null=True
    )
    image_url = models.URLField(blank=True, default="")

    activities = models.JSONField(default=list, blank=True)

    @property
    def display_image_url(self):
        if self.image_file:
            return self.image_file.url
        return self.image_url

    class Meta:
        ordering = ["day_number"]

    def __str__(self):
        return f"Day {self.day_number}: {self.title} - {self.tour.title}"


class BlogPost(models.Model):
    title = models.CharField(max_length=250, verbose_name="Title (H1)")
    slug = models.SlugField(unique=True)

    category = models.CharField(
        max_length=100,
        default="Guide"
    )

    read_time = models.CharField(
        max_length=50,
        default="4 min read"
    )

    author = models.CharField(
        max_length=100,
        default="Flavour Squad"
    )

    cover_image_file = models.ImageField(
        upload_to="blogs/",
        blank=True,
        null=True
    )
    cover_image_url = models.URLField(blank=True, default="")

    excerpt = models.TextField()
    content = models.TextField()

    vibe_tag = models.CharField(
        max_length=100,
        default="#TravelHacks"
    )

    related_tour = models.ForeignKey(
        Tour,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blogs"
    )

    # SEO Settings
    seo_title = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="SEO title",
        help_text="Recommended: 50–60 characters"
    )
    meta_description = models.TextField(
        blank=True,
        verbose_name="Meta description",
        help_text="Recommended: 150–160 characters"
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Meta keywords",
        help_text="Comma-separated keywords for local search & topics (e.g. Kashmir winter tour, Gulmarg snowfall travel guide)"
    )
    canonical_url = models.URLField(
        max_length=300,
        blank=True,
        verbose_name="Canonical URL",
        help_text="Optional custom canonical URL. Defaults to https://www.flavourholidays.com/blog/<slug>/"
    )
    image_alt = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Image alt text",
        help_text="Snow-covered mountains in Gulmarg, Kashmir"
    )
    allow_indexing = models.BooleanField(
        default=True,
        verbose_name="Allow search engines to index this page",
        help_text="Allow search engines to index this page"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def cover_image(self):
        if self.cover_image_file:
            return self.cover_image_file.url
        return self.cover_image_url

    @property
    def effective_seo_title(self):
        if self.seo_title and self.seo_title.strip():
            return self.seo_title.strip()
        return f"{self.title} | Flavour Holidays"

    @property
    def effective_meta_description(self):
        if self.meta_description and self.meta_description.strip():
            return self.meta_description.strip()
        if self.excerpt and self.excerpt.strip():
            return self.excerpt.strip()
        if self.content:
            return self.content.strip()[:160]
        return ""

    @property
    def effective_canonical_url(self):
        if self.canonical_url and self.canonical_url.strip():
            return self.canonical_url.strip()
        return f"https://www.flavourholidays.com/blog/{self.slug}/"

    @property
    def effective_image_alt(self):
        if self.image_alt and self.image_alt.strip():
            return self.image_alt.strip()
        return self.title

    def __str__(self):
        return self.title



class Vehicle(models.Model):
    name = models.CharField(max_length=150)
    model_name = models.CharField(max_length=150)
    rent_per_day = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Daily rental rate in Indian rupees.",
        verbose_name="Rent per day (₹)",
    )

    capacity_passengers = models.CharField(
        max_length=100
    )

    terrain_type = models.CharField(
        max_length=150
    )

    route_description = models.TextField(
        blank=True,
        default="",
        help_text="Routes this vehicle is suited for, shown in the homepage fleet table.",
    )

    description = models.TextField()

    image_file = models.ImageField(
        upload_to="vehicles/",
        blank=True,
        null=True
    )

    image_url = models.URLField(
        blank=True,
        default=""
    )

    badge = models.CharField(
        max_length=100,
        default="4x4 Beast"
    )

    @property
    def display_image_url(self):
        if self.image_file:
            return self.image_file.url
        return self.image_url

    def __str__(self):
        return self.name


class KashmirRouteFare(models.Model):
    destination = models.CharField(max_length=180, unique=True)
    sedan_price = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Price in Indian rupees (₹). Leave blank to show ‘Ask for quote’.",
        verbose_name="Sedan (Etios/Swift Desire) (₹)",
    )
    innova_price = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Price in Indian rupees (₹). Leave blank to show ‘Ask for quote’.",
        verbose_name="Innova (₹)",
    )
    tempo_traveller_price = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Price in Indian rupees (₹). Leave blank to show ‘Ask for quote’.",
        verbose_name="Tempo Traveler (₹)",
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Kashmir taxi route fare"
        verbose_name_plural = "Kashmir taxi route fares"

    def __str__(self):
        return self.destination


class Inquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30)

    travel_dates = models.CharField(
        max_length=100,
        blank=True
    )

    travelers_count = models.IntegerField(default=2)

    selected_tour = models.ForeignKey(
        Tour,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    vehicle_preference = models.CharField(
        max_length=100,
        blank=True
    )

    custom_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Inquiry from {self.name} ({self.phone})"


class BookingSearch(models.Model):
    selected_tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="booking_searches"
    )

    check_in = models.DateField()
    check_out = models.DateField()

    people = models.PositiveIntegerField(default=2)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.selected_tour.title} "
            f"({self.check_in} to {self.check_out})"
        )


class Testimonial(models.Model):
    client_name = models.CharField(max_length=100)

    trip_type = models.CharField(
        max_length=100
    )

    rating = models.IntegerField(default=5)

    comment = models.TextField()

    avatar_file = models.ImageField(
        upload_to="testimonials/",
        blank=True,
        null=True
    )

    avatar_url = models.URLField(
        blank=True,
        default=""
    )

    location_visited = models.CharField(
        max_length=100,
        default="Kashmir"
    )

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

    category = models.CharField(
        max_length=100,
        default="General"
    )

    def __str__(self):
        return self.question


class PlannerPlace(models.Model):
    class Region(models.TextChoices):
        KASHMIR = "kashmir", "Kashmir"
        LADAKH = "ladakh", "Ladakh"

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    region = models.CharField(max_length=20, choices=Region.choices)
    description = models.TextField(blank=True)
    cover_image_file = models.ImageField(upload_to="planner/places/", blank=True, null=True)
    cover_image_url = models.URLField(blank=True, default="")
    highlight = models.CharField(max_length=180, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["region", "sort_order", "name"]

    @property
    def cover_image(self):
        if self.cover_image_file:
            return self.cover_image_file.url
        return self.cover_image_url

    def __str__(self):
        return f"{self.name} ({self.get_region_display()})"


class PlannerStayOption(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    estimate_per_night = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Optional per-night estimate in INR. Leave blank to require a personal quote.",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Planner stay option"

    def __str__(self):
        return self.name


class PlannerTransportOption(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planner_options",
    )
    estimate_per_day = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Optional per-day estimate in INR. Leave blank to require a personal quote.",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Planner transport option"

    def __str__(self):
        return self.name


class PlannerActivity(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    estimate_amount = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Optional per-person activity estimate in INR. Leave blank to require a personal quote.",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Planner activity"

    def __str__(self):
        return self.name


class PlannerAdditionalService(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    estimate_amount = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Optional flat estimate per trip in INR. Leave blank to require a personal quote.",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Planner additional service"

    def __str__(self):
        return self.name


class PlannerBudgetBand(models.Model):
    slug = models.SlugField(unique=True)
    label = models.CharField(max_length=80)
    min_amount = models.PositiveIntegerField(blank=True, null=True)
    max_amount = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Planner budget band"

    def __str__(self):
        return self.label


class PlannerTravelStyle(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Planner travel style"

    def __str__(self):
        return self.name


class PlannerSeasonRate(models.Model):
    name = models.CharField(max_length=80)
    start_month = models.PositiveSmallIntegerField()
    start_day = models.PositiveSmallIntegerField(default=1)
    end_month = models.PositiveSmallIntegerField()
    end_day = models.PositiveSmallIntegerField(default=1)
    multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Applied to configured estimates when travel dates overlap this window.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Planner seasonal rate"

    def clean(self):
        from django.core.exceptions import ValidationError
        from datetime import date

        try:
            date(2024, self.start_month, self.start_day)
            date(2024 if (self.start_month, self.start_day) <= (self.end_month, self.end_day) else 2025, self.end_month, self.end_day)
        except (TypeError, ValueError):
            raise ValidationError("Enter valid start and end month/day values for the seasonal rate.")
        if self.multiplier is not None and self.multiplier <= 0:
            raise ValidationError({'multiplier': "The seasonal multiplier must be greater than zero."})

    def __str__(self):
        return f"{self.name} ×{self.multiplier}"


class TripInquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUOTATION_PENDING = "quotation_pending", "Quotation Pending"
        QUOTATION_SENT = "quotation_sent", "Quotation Sent"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    class BudgetScope(models.TextChoices):
        PER_PERSON = "per_person", "Per person"
        TOTAL = "total", "Total trip"

    reference_id = models.CharField(max_length=16, unique=True, db_index=True)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone_country_code = models.CharField(max_length=8, default="+91")
    phone = models.CharField(max_length=30)
    departure_date = models.DateField()
    return_date = models.DateField()
    adults = models.PositiveSmallIntegerField(default=1)
    children = models.PositiveSmallIntegerField(default=0)
    infants = models.PositiveSmallIntegerField(default=0)
    stay_option = models.ForeignKey(
        PlannerStayOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
    )
    transport_option = models.ForeignKey(
        PlannerTransportOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
    )
    budget_band = models.ForeignKey(
        PlannerBudgetBand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
    )
    budget_scope = models.CharField(
        max_length=20,
        choices=BudgetScope.choices,
        default=BudgetScope.PER_PERSON,
    )
    travel_style = models.ForeignKey(
        PlannerTravelStyle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
    )
    food_preferences = models.CharField(max_length=250, blank=True, default="")
    special_requests = models.TextField(blank=True, default="")
    accessibility_needs = models.TextField(blank=True, default="")
    additional_information = models.TextField(blank=True, default="")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.NEW, db_index=True)
    admin_notes = models.TextField(blank=True, default="")
    estimate_snapshot = models.JSONField(default=dict, blank=True)
    submit_fingerprint = models.CharField(max_length=64, db_index=True, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    places = models.ManyToManyField(PlannerPlace, through="TripInquiryPlace", related_name="inquiries")
    activities = models.ManyToManyField(PlannerActivity, through="TripInquiryActivity", related_name="inquiries")
    additional_services = models.ManyToManyField(PlannerAdditionalService, through="TripInquiryAdditionalService", related_name="inquiries")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Trip customization enquiry"

    @property
    def travelers_total(self):
        return self.adults + self.children + self.infants

    @property
    def nights(self):
        if not self.departure_date or not self.return_date:
            return 0
        delta = (self.return_date - self.departure_date).days
        return max(delta, 0)

    def __str__(self):
        return f"{self.reference_id} — {self.name}"


class TripInquiryPlace(models.Model):
    inquiry = models.ForeignKey(TripInquiry, on_delete=models.CASCADE, related_name="place_links")
    place = models.ForeignKey(PlannerPlace, on_delete=models.CASCADE)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = ("inquiry", "place")
        verbose_name = "Selected destination"


class TripInquiryActivity(models.Model):
    inquiry = models.ForeignKey(TripInquiry, on_delete=models.CASCADE, related_name="activity_links")
    activity = models.ForeignKey(PlannerActivity, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("inquiry", "activity")
        verbose_name = "Selected activity"


class TripInquiryAdditionalService(models.Model):
    inquiry = models.ForeignKey(TripInquiry, on_delete=models.CASCADE, related_name="additional_service_links")
    service = models.ForeignKey(PlannerAdditionalService, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("inquiry", "service")
        verbose_name = "Selected additional service"


class TripQuotation(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    inquiry = models.OneToOneField(TripInquiry, on_delete=models.CASCADE, related_name="quotation")
    accommodation_cost = models.PositiveIntegerField(default=0)
    transportation_cost = models.PositiveIntegerField(default=0)
    activities_cost = models.PositiveIntegerField(default=0)
    additional_charges = models.PositiveIntegerField(default=0)
    total_quotation = models.PositiveIntegerField(default=0)
    admin_notes = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Trip quotation"

    def save(self, *args, **kwargs):
        self.total_quotation = (
            self.accommodation_cost
            + self.transportation_cost
            + self.activities_cost
            + self.additional_charges
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Quote {self.inquiry.reference_id}: ₹{self.total_quotation}"

