from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.throttling import AnonRateThrottle
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from .models import (
    Destination, Tour, TourCheckpoint, BlogPost, Vehicle, KashmirRouteFare, Inquiry, BookingSearch,
    Testimonial, FAQ, PlannerPlace, PlannerStayOption, PlannerTransportOption,
    PlannerActivity, PlannerAdditionalService, PlannerBudgetBand, PlannerTravelStyle, TripInquiry,
    PlannerSeasonRate, TripInquiryPlace, TripInquiryActivity, TripQuotation,
)
from .serializers import (
    DestinationSerializer, TourListSerializer, TourDetailSerializer,
    TourCheckpointSerializer, BlogPostSerializer, VehicleSerializer, KashmirRouteFareSerializer,
    InquirySerializer, BookingSearchSerializer, TestimonialSerializer, FAQSerializer,
    PlannerPlaceSerializer, PlannerStayOptionSerializer, PlannerTransportOptionSerializer,
    PlannerActivitySerializer, PlannerAdditionalServiceSerializer, PlannerBudgetBandSerializer, PlannerTravelStyleSerializer,
    TripInquiryCreateSerializer, TripInquiryAdminSerializer, TripQuotationSerializer,
)
from .planner import build_estimate, generate_reference_id, inquiry_fingerprint, whatsapp_url


class TripPlannerAnonThrottle(AnonRateThrottle):
    scope = 'trip_planner'


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def trip_planner_options(request):
    return Response({
        'destinations': PlannerPlaceSerializer(PlannerPlace.objects.filter(is_active=True), many=True, context={'request': request}).data,
        'stays': PlannerStayOptionSerializer(PlannerStayOption.objects.filter(is_active=True), many=True).data,
        'transports': PlannerTransportOptionSerializer(PlannerTransportOption.objects.filter(is_active=True).select_related('vehicle'), many=True).data,
        'activities': PlannerActivitySerializer(PlannerActivity.objects.filter(is_active=True), many=True).data,
        'additional_services': PlannerAdditionalServiceSerializer(PlannerAdditionalService.objects.filter(is_active=True), many=True).data,
        'budgets': PlannerBudgetBandSerializer(PlannerBudgetBand.objects.filter(is_active=True), many=True).data,
        'travel_styles': PlannerTravelStyleSerializer(PlannerTravelStyle.objects.filter(is_active=True), many=True).data,
        'seasonal_rates': list(PlannerSeasonRate.objects.filter(is_active=True).values(
            'name', 'start_month', 'start_day', 'end_month', 'end_day', 'multiplier'
        )),
    })


@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([TripPlannerAnonThrottle])
def create_trip_inquiry(request):
    if request.method == 'GET':
        if not request.user.is_staff:
            return Response({'detail': 'Administrator access is required.'}, status=status.HTTP_403_FORBIDDEN)
        inquiries = TripInquiry.objects.select_related(
            'stay_option', 'transport_option', 'budget_band', 'travel_style'
        ).prefetch_related('places', 'activities', 'additional_services')
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            inquiries = inquiries.filter(Q(name__icontains=search) | Q(phone__icontains=search) | Q(reference_id__icontains=search))
        for key in ('status', 'departure_date', 'budget_band__slug'):
            value = request.query_params.get(key)
            if value:
                inquiries = inquiries.filter(**{key: value})
        destination = request.query_params.get('destination')
        if destination:
            inquiries = inquiries.filter(places__slug=destination)
        paginator = LimitOffsetPagination()
        paginator.default_limit = 50
        page = paginator.paginate_queryset(inquiries, request)
        return paginator.get_paginated_response(TripInquiryAdminSerializer(page, many=True, context={'request': request}).data)

    # A honeypot field catches simple bots without exposing an extra model field.
    if request.data.get('website'):
        return Response({'status': 'success', 'message': 'Enquiry received.'}, status=status.HTTP_201_CREATED)
    serializer = TripInquiryCreateSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    place_slugs = data.pop('destination_slugs')
    activity_slugs = data.pop('activity_slugs', [])
    additional_service_slugs = data.pop('additional_service_slugs', [])
    stay_slug = data.pop('stay_slug', None)
    transport_slug = data.pop('transport_slug', None)
    budget_slug = data.pop('budget_slug', None)
    style_slug = data.pop('travel_style_slug', None)
    fingerprint = inquiry_fingerprint(
        email=data['email'], phone=data['phone'], departure=data['departure_date'],
        return_date=data['return_date'], place_slugs=place_slugs,
    )
    recent = TripInquiry.objects.filter(
        submit_fingerprint=fingerprint,
        created_at__gte=timezone.now() - timedelta(minutes=10),
    ).first()
    if recent:
        return Response({
            'status': 'success', 'reference_id': recent.reference_id,
            'message': 'We have already received this trip enquiry.',
            'estimate': recent.estimate_snapshot, 'whatsapp_url': whatsapp_url(recent),
        }, status=status.HTTP_200_OK)

    places = list(PlannerPlace.objects.filter(is_active=True, slug__in=place_slugs))
    activities = list(PlannerActivity.objects.filter(is_active=True, slug__in=activity_slugs))
    additional_services = list(PlannerAdditionalService.objects.filter(is_active=True, slug__in=additional_service_slugs))
    stay = PlannerStayOption.objects.filter(is_active=True, slug=stay_slug).first() if stay_slug else None
    transport = PlannerTransportOption.objects.filter(is_active=True, slug=transport_slug).first() if transport_slug else None
    budget = PlannerBudgetBand.objects.filter(is_active=True, slug=budget_slug).first() if budget_slug else None
    style = PlannerTravelStyle.objects.filter(is_active=True, slug=style_slug).first() if style_slug else None
    nights = (data['return_date'] - data['departure_date']).days
    estimate = build_estimate(
        nights=nights, travelers=data['adults'] + data['children'] + data['infants'],
        stay=stay, transport=transport, activities=activities,
        additional_services=additional_services,
        departure=data['departure_date'], return_date=data['return_date'],
    )
    with transaction.atomic():
        inquiry = TripInquiry.objects.create(
            **data, reference_id=generate_reference_id(), stay_option=stay,
            transport_option=transport, budget_band=budget, travel_style=style,
            submit_fingerprint=fingerprint, estimate_snapshot=estimate,
        )
        TripInquiryPlace.objects.bulk_create([
            TripInquiryPlace(inquiry=inquiry, place=place, sort_order=index)
            for index, place in enumerate(places)
        ])
        TripInquiryActivity.objects.bulk_create([
            TripInquiryActivity(inquiry=inquiry, activity=activity) for activity in activities
        ])
        inquiry.additional_services.add(*additional_services)
    return Response({
        'status': 'success', 'reference_id': inquiry.reference_id,
        'message': 'Your trip enquiry has been received. Our travel team will be in touch shortly.',
        'estimate': estimate, 'whatsapp_url': whatsapp_url(inquiry),
    }, status=status.HTTP_201_CREATED)


class TripInquiryViewSet(viewsets.ModelViewSet):
    queryset = TripInquiry.objects.select_related(
        'stay_option', 'transport_option', 'budget_band', 'travel_style', 'quotation'
    ).prefetch_related('places', 'activities', 'additional_services')
    serializer_class = TripInquiryAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'reference_id'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'phone', 'reference_id', 'email']
    ordering_fields = ['created_at', 'departure_date', 'status']
    ordering = ['-created_at']

    @action(detail=True, methods=['post', 'patch'], url_path='quotation')
    def quotation(self, request, reference_id=None):
        inquiry = self.get_object()
        instance = getattr(inquiry, 'quotation', None)
        serializer = TripQuotationSerializer(instance, data=request.data, partial=request.method == 'PATCH')
        serializer.is_valid(raise_exception=True)
        quotation = serializer.save(inquiry=inquiry)
        return Response(TripQuotationSerializer(quotation).data, status=status.HTTP_200_OK if instance else status.HTTP_201_CREATED)

class DestinationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    lookup_field = 'slug'

class TourViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tour.objects.all().select_related('destination').prefetch_related('checkpoints', 'pricing_options')
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'vibe_tag', 'destination__name', 'overview']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TourDetailSerializer
        return TourListSerializer

    @action(detail=False, methods=['get'])
    def featured(self, request):
        tours = self.queryset.filter(is_featured=True)
        serializer = TourListSerializer(tours, many=True)
        return Response(serializer.data)

class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BlogPost.objects.all().order_by('-created_at')
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'

class VehicleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer


class KashmirRouteFareViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = KashmirRouteFare.objects.filter(is_active=True)
    serializer_class = KashmirRouteFareSerializer

class InquiryViewSet(viewsets.ModelViewSet):
    queryset = Inquiry.objects.all()
    serializer_class = InquirySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "status": "success",
            "message": "Pack your bags! Our travel expert will contact you via WhatsApp / Phone shortly.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

class BookingSearchViewSet(viewsets.ModelViewSet):
    queryset = BookingSearch.objects.all().select_related('selected_tour')
    serializer_class = BookingSearchSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking_search = serializer.save()
        selected_tour = booking_search.selected_tour

        matching_tours = Tour.objects.filter(
            destination=selected_tour.destination
        ).select_related('destination').prefetch_related('checkpoints')

        blogs = BlogPost.objects.filter(related_tour__in=matching_tours).order_by('-created_at')

        return Response({
            'status': 'success',
            'message': 'Booking search saved.',
            'search': serializer.data,
            'tours': TourListSerializer(matching_tours, many=True, context={'request': request}).data,
            'blogs': BlogPostSerializer(blogs, many=True, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class TestimonialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer

class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
