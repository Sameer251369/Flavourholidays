import json
import cloudinary.exceptions
import requests.exceptions
from django.contrib import admin
from django import forms
from django.contrib import messages
from django.db import transaction

from flavour_backend.cloudinary_utils import log_upload_failure
from .models import (
    Destination, Tour, TourPricing, TourCheckpoint, BlogPost, Vehicle, KashmirRouteFare, Inquiry,
    Testimonial, FAQ, PlannerPlace, PlannerStayOption, PlannerTransportOption,
    PlannerActivity, PlannerAdditionalService, PlannerBudgetBand, PlannerTravelStyle, PlannerSeasonRate,
    TripInquiry, TripInquiryPlace, TripInquiryActivity, TripInquiryAdditionalService, TripQuotation,
)

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


class TourPricingInline(admin.TabularInline):
    model = TourPricing
    extra = 0
    fields = ("audience", "price", "note")
    verbose_name = "Audience price"
    verbose_name_plural = "Audience pricing (group, family, couple, friends, per person)"

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
    inlines = [TourCheckpointInline, TourPricingInline]
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
    list_display = ('name', 'model_name', 'rent_per_day', 'capacity_passengers', 'badge')
    search_fields = ('name', 'model_name', 'description')
    fields = ('name', 'model_name', 'rent_per_day', 'capacity_passengers', 'terrain_type', 'badge', 'description', 'image_file', 'image_url')


@admin.register(KashmirRouteFare)
class KashmirRouteFareAdmin(admin.ModelAdmin):
    list_display = ('destination', 'sedan_price', 'innova_price', 'tempo_traveller_price', 'sort_order', 'is_active')
    list_editable = ('sedan_price', 'innova_price', 'tempo_traveller_price', 'sort_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('destination',)
    ordering = ('sort_order', 'id')
    fields = ('destination', 'sedan_price', 'innova_price', 'tempo_traveller_price', 'sort_order', 'is_active')

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


class TripInquiryPlaceInline(admin.TabularInline):
    model = TripInquiryPlace
    extra = 0
    autocomplete_fields = ('place',)


class TripInquiryActivityInline(admin.TabularInline):
    model = TripInquiryActivity
    extra = 0
    autocomplete_fields = ('activity',)


class TripInquiryAdditionalServiceInline(admin.TabularInline):
    model = TripInquiryAdditionalService
    extra = 0
    autocomplete_fields = ('service',)


class TripQuotationInline(admin.StackedInline):
    model = TripQuotation
    extra = 0
    max_num = 1
    readonly_fields = ('total_quotation', 'created_at', 'updated_at')


@admin.register(TripInquiry)
class TripInquiryAdmin(admin.ModelAdmin):
    list_display = ('reference_id', 'name', 'customer_contact', 'departure_date', 'return_date', 'status', 'created_at')
    list_filter = ('status', 'departure_date', 'budget_band', 'travel_style', 'places')
    search_fields = ('reference_id', 'name', 'phone', 'email')
    readonly_fields = ('reference_id', 'created_at', 'updated_at', 'travelers_total', 'nights', 'estimate_snapshot')
    autocomplete_fields = ('stay_option', 'transport_option', 'budget_band', 'travel_style')
    inlines = (TripInquiryPlaceInline, TripInquiryActivityInline, TripInquiryAdditionalServiceInline, TripQuotationInline)
    list_select_related = ('stay_option', 'transport_option', 'budget_band', 'travel_style')
    fieldsets = (
        ('Customer', {'fields': ('reference_id', ('name', 'email'), ('phone_country_code', 'phone'))}),
        ('Travel details', {'fields': (('departure_date', 'return_date'), ('adults', 'children', 'infants'), 'travelers_total', 'nights')}),
        ('Preferences', {'fields': (('stay_option', 'transport_option'), ('budget_band', 'budget_scope'), 'travel_style', 'food_preferences', 'special_requests', 'accessibility_needs', 'additional_information')}),
        ('Management', {'fields': ('status', 'admin_notes', 'estimate_snapshot', ('created_at', 'updated_at'))}),
    )

    @admin.display(description='Phone', ordering='phone')
    def customer_contact(self, obj):
        number = ''.join(character for character in f'{obj.phone_country_code}{obj.phone}' if character.isdigit())
        return format_html('<a href="tel:+{}">{}</a> · <a href="https://wa.me/{}" target="_blank" rel="noopener">WhatsApp</a>', number, f'{obj.phone_country_code} {obj.phone}', number)


@admin.register(PlannerPlace)
class PlannerPlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'is_active', 'sort_order')
    list_filter = ('region', 'is_active')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PlannerStayOption)
class PlannerStayOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'estimate_per_night', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')


@admin.register(PlannerTransportOption)
class PlannerTransportOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle', 'estimate_per_day', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')


@admin.register(PlannerActivity)
class PlannerActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'estimate_amount', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')


@admin.register(PlannerAdditionalService)
class PlannerAdditionalServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'estimate_amount', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')


@admin.register(PlannerBudgetBand)
class PlannerBudgetBandAdmin(admin.ModelAdmin):
    list_display = ('label', 'min_amount', 'max_amount', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('label', 'slug')


@admin.register(PlannerTravelStyle)
class PlannerTravelStyleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')


@admin.register(PlannerSeasonRate)
class PlannerSeasonRateAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_month', 'start_day', 'end_month', 'end_day', 'multiplier', 'is_active')
    list_filter = ('is_active',)
