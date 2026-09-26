from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Destination, Tour, TourCheckpoint, BlogPost, Vehicle, Inquiry, BookingSearch, Testimonial, FAQ
from .serializers import (
    DestinationSerializer, TourListSerializer, TourDetailSerializer,
    TourCheckpointSerializer, BlogPostSerializer, VehicleSerializer,
    InquirySerializer, BookingSearchSerializer, TestimonialSerializer, FAQSerializer
)

class DestinationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    lookup_field = 'slug'

class TourViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tour.objects.all().select_related('destination').prefetch_related('checkpoints')
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
