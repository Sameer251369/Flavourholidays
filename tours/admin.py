import json
from django.contrib import admin
from django import forms
from .models import Destination, Tour, TourCheckpoint, BlogPost, Vehicle, Inquiry, Testimonial, FAQ

def parse_list_input(val):
    if not val:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        val_str = val.strip()
        if val_str.startswith('[') and val_str.endswith(']'):
            try:
                return json.loads(val_str)
            except Exception:
                pass
        # Fallback to newline-separated items
        return [item.strip() for item in val_str.split('\n') if item.strip()]
    return []

class TourAdminForm(forms.ModelForm):
    inclusions = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter each inclusion on a new line or as a JSON array'}),
        required=False,
        help_text="Enter each inclusion on a new line or as JSON list"
    )
    exclusions = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter each exclusion on a new line or as a JSON array'}),
        required=False,
        help_text="Enter each exclusion on a new line or as JSON list"
    )

    class Meta:
        model = Tour
        fields = '__all__'

    def clean_inclusions(self):
        return parse_list_input(self.cleaned_data.get('inclusions'))

    def clean_exclusions(self):
        return parse_list_input(self.cleaned_data.get('exclusions'))

class TourCheckpointAdminForm(forms.ModelForm):
    activities = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'e.g.\nAirport Transfer\nHouseboat Check-in\n1-Hour Sunset Shikara\nWazwan Tasting Dinner'}),
        required=False,
        help_text="Enter included day activities (one activity per line or as JSON list)"
    )

    class Meta:
        model = TourCheckpoint
        fields = '__all__'

    def clean_activities(self):
        return parse_list_input(self.cleaned_data.get('activities'))

class TourCheckpointInline(admin.StackedInline):
    model = TourCheckpoint
    form = TourCheckpointAdminForm
    extra = 1
    fieldsets = (
        (None, {
            'fields': (('day_number', 'title', 'location_name', 'altitude'), 'description')
        }),
        ('Highlights & Image Upload', {
            'fields': ('insta_spot', 'vibe_highlight', 'image_file', 'image_url', 'activities')
        }),
    )

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'altitude_range', 'best_time')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fields = ('name', 'slug', 'description', 'altitude_range', 'best_time', 'cover_image_file', 'cover_image_url')

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    form = TourAdminForm
    list_display = ('title', 'destination', 'starting_price', 'duration_days', 'duration_nights', 'difficulty', 'is_featured')
    list_filter = ('destination', 'difficulty', 'is_featured')
    search_fields = ('title', 'overview', 'tagline', 'vibe_tag')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [TourCheckpointInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'destination', 'tagline', 'vibe_tag', 'is_featured')
        }),
        ('Pricing & Duration', {
            'fields': ('duration_days', 'duration_nights', 'starting_price', 'difficulty')
        }),
        ('Cover Image & Overview', {
            'fields': ('cover_image_file', 'cover_image_url', 'gallery_urls', 'overview')
        }),
        ('Inclusions & Exclusions', {
            'fields': ('inclusions', 'exclusions')
        }),
    )

@admin.register(TourCheckpoint)
class TourCheckpointAdmin(admin.ModelAdmin):
    form = TourCheckpointAdminForm
    list_display = ('tour', 'day_number', 'title', 'location_name', 'altitude')
    list_filter = ('tour',)
    search_fields = ('title', 'location_name', 'description')
    fields = ('tour', 'day_number', 'title', 'location_name', 'altitude', 'description', 'insta_spot', 'vibe_highlight', 'image_file', 'image_url', 'activities')

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'read_time', 'created_at')
    list_filter = ('category', 'author')
    search_fields = ('title', 'excerpt', 'content')
    prepopulated_fields = {'slug': ('title',)}
    fields = ('title', 'slug', 'category', 'read_time', 'author', 'vibe_tag', 'related_tour', 'cover_image_file', 'cover_image_url', 'excerpt', 'content')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_name', 'capacity_passengers', 'badge')
    search_fields = ('name', 'model_name', 'description')
    fields = ('name', 'model_name', 'capacity_passengers', 'terrain_type', 'badge', 'description', 'image_file', 'image_url')

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'selected_tour', 'travelers_count', 'created_at')
    list_filter = ('created_at', 'selected_tour')
    search_fields = ('name', 'email', 'phone', 'custom_notes')
    readonly_fields = ('created_at',)

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'trip_type', 'rating', 'location_visited')
    list_filter = ('rating', 'trip_type')
    search_fields = ('client_name', 'comment')
    fields = ('client_name', 'trip_type', 'rating', 'location_visited', 'comment', 'avatar_file', 'avatar_url')

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category')
    list_filter = ('category',)
    search_fields = ('question', 'answer')


