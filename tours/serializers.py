from rest_framework import serializers
from .models import Destination, Tour, TourCheckpoint, BlogPost, Vehicle, Inquiry, BookingSearch, Testimonial, FAQ

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

class TourListSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    checkpoints = TourCheckpointSerializer(many=True, read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Tour
        fields = [
            'id', 'title', 'slug', 'destination', 'destination_name',
            'tagline', 'vibe_tag', 'duration_days', 'duration_nights',
            'starting_price', 'difficulty', 'cover_image', 'gallery_urls',
            'overview', 'inclusions', 'exclusions', 'is_featured', 'checkpoints'
        ]

    def get_cover_image(self, obj):
        request = self.context.get('request')
        return resolve_image_url(request, obj.cover_image)

class TourDetailSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    checkpoints = TourCheckpointSerializer(many=True, read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Tour
        fields = '__all__'

    def get_cover_image(self, obj):
        request = self.context.get('request')
        return resolve_image_url(request, obj.cover_image)

class BlogPostSerializer(serializers.ModelSerializer):
    related_tour_title = serializers.CharField(source='related_tour.title', read_only=True, allow_null=True)
    related_tour_slug = serializers.CharField(source='related_tour.slug', read_only=True, allow_null=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = '__all__'

    def get_cover_image(self, obj):
        request = self.context.get('request')
        return resolve_image_url(request, obj.cover_image)

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

