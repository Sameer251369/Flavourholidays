from rest_framework import serializers
from django.utils import timezone
from .models import (
    Destination, Tour, TourPricing, TourCheckpoint, BlogPost, Vehicle, Inquiry,
    BookingSearch, Testimonial, FAQ, PlannerPlace, PlannerStayOption,
    PlannerTransportOption, PlannerActivity, PlannerAdditionalService, PlannerBudgetBand,
    PlannerTravelStyle, TripInquiry, TripInquiryPlace, TripInquiryActivity,
    TripQuotation,
)

def resolve_image_url(request, path_or_url):
    if not path_or_url:
        return ""
    if path_or_url.startswith('http://') or path_or_url.startswith('https://'):
        return path_or_url
    if request:
        return request.build_absolute_uri(path_or_url)
    return path_or_url

class DestinationSerializer(serializers.ModelSerializer):
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = '__all__'

    def get_cover_image(self, obj):
        request = self.context.get('request')
        return resolve_image_url(request, obj.cover_image)

class TourCheckpointSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = TourCheckpoint
        fields = '__all__'

    def get_image_url(self, obj):
        request = self.context.get('request')
        return resolve_image_url(request, obj.display_image_url)


class TourPricingSerializer(serializers.ModelSerializer):
    audience_label = serializers.CharField(source="get_audience_display", read_only=True)

    class Meta:
        model = TourPricing
        fields = ["id", "audience", "audience_label", "price", "note"]

class TourListSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    checkpoints = TourCheckpointSerializer(many=True, read_only=True)
    cover_image = serializers.SerializerMethodField()
    pricing_options = TourPricingSerializer(many=True, read_only=True)

    class Meta:
        model = Tour
        fields = [
            'id', 'title', 'slug', 'destination', 'destination_name',
            'tagline', 'vibe_tag', 'duration_days', 'duration_nights',
            'starting_price', 'difficulty', 'cover_image', 'gallery_urls',
            'overview', 'inclusions', 'exclusions', 'is_featured', 'checkpoints', 'pricing_options'
        ]

    def get_cover_image(self, obj):
        request = self.context.get('request')
        return resolve_image_url(request, obj.cover_image)

class TourDetailSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    checkpoints = TourCheckpointSerializer(many=True, read_only=True)
    cover_image = serializers.SerializerMethodField()
    pricing_options = TourPricingSerializer(many=True, read_only=True)

    class Meta:
        model = Tour
        fields = '__all__'
        read_only_fields = ("pricing_options",)

    def get_cover_image(self, obj):
        request = self.context.get('request')
        return resolve_image_url(request, obj.cover_image)

class BlogPostSerializer(serializers.ModelSerializer):
    related_tour_title = serializers.CharField(source='related_tour.title', read_only=True, allow_null=True)
    related_tour_slug = serializers.CharField(source='related_tour.slug', read_only=True, allow_null=True)
    cover_image = serializers.SerializerMethodField()
    canonical_url = serializers.SerializerMethodField()
    seo_title = serializers.SerializerMethodField()
    meta_description = serializers.SerializerMethodField()
    image_alt = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = '__all__'

    def get_cover_image(self, obj):
        request = self.context.get('request')
        return resolve_image_url(request, obj.cover_image)

    def get_canonical_url(self, obj):
        return obj.effective_canonical_url

    def get_seo_title(self, obj):
        return obj.effective_seo_title

    def get_meta_description(self, obj):
        return obj.effective_meta_description

    def get_image_alt(self, obj):
        return obj.effective_image_alt


class VehicleSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = '__all__'

    def get_image_url(self, obj):
        request = self.context.get('request')
        return resolve_image_url(request, obj.display_image_url)

class InquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = '__all__'

class BookingSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingSearch
        fields = '__all__'

    def validate(self, attrs):
        if attrs['check_out'] < attrs['check_in']:
            raise serializers.ValidationError({'check_out': 'Check-out must be on or after check-in.'})
        if attrs['people'] < 1:
            raise serializers.ValidationError({'people': 'People must be at least 1.'})
        return attrs

class TestimonialSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Testimonial
        fields = '__all__'

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        return resolve_image_url(request, obj.display_avatar_url)

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'


class PlannerPlaceSerializer(serializers.ModelSerializer):
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = PlannerPlace
        fields = ['slug', 'name', 'region', 'description', 'cover_image', 'highlight']

    def get_cover_image(self, obj):
        return resolve_image_url(self.context.get('request'), obj.cover_image)


class PlannerStayOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannerStayOption
        fields = ['slug', 'name', 'description', 'estimate_per_night']


class PlannerTransportOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannerTransportOption
        fields = ['slug', 'name', 'description', 'estimate_per_day']


class PlannerActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannerActivity
        fields = ['slug', 'name', 'description', 'estimate_amount']


class PlannerAdditionalServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannerAdditionalService
        fields = ['slug', 'name', 'description', 'estimate_amount']


class PlannerBudgetBandSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannerBudgetBand
        fields = ['slug', 'label', 'min_amount', 'max_amount']


class PlannerTravelStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannerTravelStyle
        fields = ['slug', 'name']


class TripInquiryCreateSerializer(serializers.ModelSerializer):
    phone_country_code = serializers.RegexField(regex=r'^\+\d{1,4}$', max_length=8, default='+91')
    phone = serializers.RegexField(regex=r'^[0-9\s()+-]{6,30}$', max_length=30, trim_whitespace=True)
    special_requests = serializers.CharField(max_length=3000, required=False, allow_blank=True)
    accessibility_needs = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    additional_information = serializers.CharField(max_length=3000, required=False, allow_blank=True)
    destination_slugs = serializers.ListField(child=serializers.SlugField(), allow_empty=False, write_only=True)
    activity_slugs = serializers.ListField(child=serializers.SlugField(), required=False, write_only=True)
    additional_service_slugs = serializers.ListField(child=serializers.SlugField(), required=False, write_only=True)
    stay_slug = serializers.SlugField(required=False, allow_null=True, write_only=True)
    transport_slug = serializers.SlugField(required=False, allow_null=True, write_only=True)
    budget_slug = serializers.SlugField(required=False, allow_null=True, write_only=True)
    travel_style_slug = serializers.SlugField(required=False, allow_null=True, write_only=True)
    travelers_total = serializers.IntegerField(read_only=True)
    nights = serializers.IntegerField(read_only=True)

    class Meta:
        model = TripInquiry
        fields = [
            'reference_id', 'name', 'email', 'phone_country_code', 'phone',
            'departure_date', 'return_date', 'adults', 'children', 'infants',
            'destination_slugs', 'activity_slugs', 'additional_service_slugs', 'stay_slug', 'transport_slug',
            'budget_slug', 'budget_scope', 'travel_style_slug', 'food_preferences',
            'special_requests', 'accessibility_needs', 'additional_information',
            'travelers_total', 'nights', 'estimate_snapshot', 'status', 'created_at',
        ]
        read_only_fields = ['reference_id', 'estimate_snapshot', 'status', 'created_at']

    def validate(self, attrs):
        if attrs['departure_date'] < timezone.localdate():
            raise serializers.ValidationError({'departure_date': 'Departure date cannot be in the past.'})
        if attrs['return_date'] <= attrs['departure_date']:
            raise serializers.ValidationError({'return_date': 'Return date must be after departure date.'})
        adults = attrs.get('adults', 1)
        children = attrs.get('children', 0)
        infants = attrs.get('infants', 0)
        if adults < 1:
            raise serializers.ValidationError({'adults': 'At least one adult is required.'})
        if adults > 20 or children > 20 or infants > 10 or adults + children + infants > 30:
            raise serializers.ValidationError({'adults': 'Please contact us for groups larger than 30 travellers.'})
        if len(''.join(character for character in attrs['phone'] if character.isdigit())) < 6:
            raise serializers.ValidationError({'phone': 'Enter a valid phone number.'})
        if attrs.get('budget_scope', TripInquiry.BudgetScope.PER_PERSON) not in TripInquiry.BudgetScope.values:
            raise serializers.ValidationError({'budget_scope': 'Choose per-person or total-trip budget.'})
        for field, model in [
            ('destination_slugs', PlannerPlace), ('activity_slugs', PlannerActivity),
            ('additional_service_slugs', PlannerAdditionalService),
        ]:
            slugs = attrs.get(field, [])
            if len(slugs) != len(set(slugs)):
                raise serializers.ValidationError({field: 'Selections must not contain duplicates.'})
            found = set(model.objects.filter(is_active=True, slug__in=slugs).values_list('slug', flat=True))
            if found != set(slugs):
                raise serializers.ValidationError({field: 'One or more selected options are unavailable.'})
        for field, model in [
            ('stay_slug', PlannerStayOption), ('transport_slug', PlannerTransportOption),
            ('budget_slug', PlannerBudgetBand), ('travel_style_slug', PlannerTravelStyle),
        ]:
            slug = attrs.get(field)
            if slug and not model.objects.filter(is_active=True, slug=slug).exists():
                raise serializers.ValidationError({field: 'Selected option is unavailable.'})
        return attrs


class TripInquiryAdminSerializer(serializers.ModelSerializer):
    destinations = PlannerPlaceSerializer(source='places', many=True, read_only=True)
    activities = PlannerActivitySerializer(many=True, read_only=True)
    additional_services = PlannerAdditionalServiceSerializer(many=True, read_only=True)
    stay = serializers.CharField(source='stay_option.name', read_only=True)
    transport = serializers.CharField(source='transport_option.name', read_only=True)
    budget = serializers.CharField(source='budget_band.label', read_only=True)
    travel_style = serializers.CharField(source='travel_style.name', read_only=True)

    class Meta:
        model = TripInquiry
        fields = '__all__'
        read_only_fields = ['reference_id', 'created_at', 'updated_at', 'submit_fingerprint']


class TripQuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripQuotation
        fields = ['accommodation_cost', 'transportation_cost', 'activities_cost', 'additional_charges', 'total_quotation', 'admin_notes', 'status', 'created_at', 'updated_at']
        read_only_fields = ['total_quotation', 'created_at', 'updated_at']

    def validate(self, attrs):
        for field in ('accommodation_cost', 'transportation_cost', 'activities_cost', 'additional_charges'):
            if attrs.get(field, 0) > 100_000_000:
                raise serializers.ValidationError({field: 'Amount is above the supported limit.'})
        return attrs

