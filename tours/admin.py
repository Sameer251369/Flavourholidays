import json
import cloudinary.exceptions
import requests.exceptions
from django.contrib import admin
from django import forms
from django.contrib import messages
from django.db import transaction

from flavour_backend.cloudinary_utils import log_upload_failure
from .models import Destination, Tour, TourCheckpoint, BlogPost, Vehicle, Inquiry, Testimonial, FAQ

IMAGE_STORAGE_ERRORS = (cloudinary.exceptions.Error, requests.exceptions.RequestException)


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

    def save_model(self, request, obj, form, change):
        previous_image = form.initial.get('cover_image_file')
        previous_image_name = getattr(previous_image, 'name', previous_image) or ''
        try:
            with transaction.atomic():
                super().save_model(request, obj, form, change)
        except IMAGE_STORAGE_ERRORS as exc:
            if not form.files.get(form.add_prefix('cover_image_file')):
                raise

            safe_error = log_upload_failure(
                'tour cover',
                exc,
                tour_slug=getattr(obj, 'slug', None),
            )
            obj.cover_image_file = previous_image_name or None
            form.cleaned_data['cover_image_file'] = previous_image_name or None
            messages.warning(
                request,
                "The tour was saved, but its new cover image could not be uploaded. "
                "The previous image or the cover image URL will be used instead. "
                f"Details: {safe_error}"
            )
            super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        try:
            with transaction.atomic():
                super().save_formset(request, form, formset, change)
        except IMAGE_STORAGE_ERRORS as exc:
            failed_image_forms = [
                inline_form
                for inline_form in formset.forms
                if inline_form.files.get(inline_form.add_prefix('image_file'))
            ]
            if not failed_image_forms:
                raise

            safe_error = log_upload_failure(
                'tour checkpoint',
                exc,
                tour_slug=getattr(form.instance, 'slug', None),
                checkpoint_count=len(failed_image_forms),
            )
            for inline_form in failed_image_forms:
                previous_image = inline_form.initial.get('image_file')
                if hasattr(previous_image, 'name'):
                    previous_image = previous_image.name
                inline_form.instance.image_file = previous_image or None
                inline_form.cleaned_data['image_file'] = previous_image or None

            super().save_formset(request, form, formset, change)
            messages.warning(
                request,
                "The tour checkpoints were saved, but one or more new checkpoint images "
                "could not be uploaded. Previous images were kept where available. "
                f"Details: {safe_error}"
            )

@admin.register(TourCheckpoint)
class TourCheckpointAdmin(admin.ModelAdmin):
    form = TourCheckpointAdminForm
    list_display = ('tour', 'day_number', 'title', 'location_name', 'altitude')
    list_filter = ('tour',)
    search_fields = ('title', 'location_name', 'description')
    fields = ('tour', 'day_number', 'title', 'location_name', 'altitude', 'description', 'insta_spot', 'vibe_highlight', 'image_file', 'image_url', 'activities')

from django.utils.html import format_html

class BlogPostAdminForm(forms.ModelForm):
    seo_title = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Kashmir in Winter 2026–27: Travel Guide | Flavour Holidays', 'style': 'width: 100%; max-width: 680px;'}),
        required=False,
        help_text="Recommended: 50–60 characters"
    )
    meta_description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Plan your Kashmir winter trip with our complete guide to weather, snowfall...', 'style': 'width: 100%; max-width: 680px;'}),
        required=False,
        help_text="Recommended: 150–160 characters"
    )
    meta_keywords = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'kashmir in winter, kashmir snowfall guide, gulmarg snow tour', 'style': 'width: 100%; max-width: 680px;'}),
        required=False,
        help_text="Comma-separated keywords for local search & topics (e.g. Kashmir winter tour, Gulmarg snowfall travel guide)"
    )
    canonical_url = forms.URLField(
        widget=forms.URLInput(attrs={'placeholder': 'https://www.flavourholidays.com/blog/kashmir-in-winter-2026/', 'style': 'width: 100%; max-width: 680px;'}),
        required=False,
        help_text="Optional custom canonical URL. Defaults to https://www.flavourholidays.com/blog/<slug>/"
    )

    class Meta:
        model = BlogPost
        fields = '__all__'


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    form = BlogPostAdminForm
    list_display = ('title', 'category', 'author', 'read_time', 'allow_indexing', 'created_at')
    list_filter = ('category', 'author', 'allow_indexing')
    search_fields = ('title', 'seo_title', 'meta_description', 'meta_keywords', 'excerpt', 'content')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('cover_image_preview',)

    fieldsets = (
        (None, {
            'fields': (
                'title',
                'slug',
                'category',
                'read_time',
                'author',
                'vibe_tag',
                'related_tour',
            )
        }),
        ('SEO Settings', {
            'fields': (
                'seo_title',
                'meta_description',
                'meta_keywords',
                'canonical_url',
                'cover_image_file',
                'cover_image_url',
                'cover_image_preview',
                'image_alt',
                'allow_indexing',
            )
        }),
        ('Blog Content', {
            'fields': (
                'excerpt',
                'content',
            )
        }),
    )

    def cover_image_preview(self, obj):
        image_url = obj.cover_image if obj else None
        if image_url:
            return format_html(
                '<img src="{}" alt="{}" style="max-height: 80px; max-width: 160px; border-radius: 6px; object-fit: cover; box-shadow: 0 1px 3px rgba(0,0,0,0.2);" />',
                image_url,
                obj.effective_image_alt or obj.title
            )
        return "No image uploaded yet"
    cover_image_preview.short_description = "Cover Preview"

    def save_model(self, request, obj, form, change):
        previous_image = form.initial.get('cover_image_file')
        previous_image_name = getattr(previous_image, 'name', previous_image) or ''
        try:
            with transaction.atomic():
                super().save_model(request, obj, form, change)
        except IMAGE_STORAGE_ERRORS as exc:
            if not form.files.get(form.add_prefix('cover_image_file')):
                raise

            safe_error = log_upload_failure(
                'blog post cover',
                exc,
                tour_slug=getattr(obj, 'slug', None),
            )
            obj.cover_image_file = previous_image_name or None
            form.cleaned_data['cover_image_file'] = previous_image_name or None
            messages.warning(
                request,
                "The blog post was saved, but its new cover image could not be uploaded. "
                "The previous image or the cover image URL will be used instead. "
                f"Details: {safe_error}"
            )
            super().save_model(request, obj, form, change)


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
