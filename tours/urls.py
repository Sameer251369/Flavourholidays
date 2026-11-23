from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DestinationViewSet, TourViewSet, BlogPostViewSet,
    VehicleViewSet, KashmirRouteFareViewSet, InquiryViewSet, BookingSearchViewSet, TestimonialViewSet, FAQViewSet,
    TripInquiryViewSet, trip_planner_options, create_trip_inquiry,
)

router = DefaultRouter()
router.register(r'destinations', DestinationViewSet, basename='destination')
router.register(r'tours', TourViewSet, basename='tour')
router.register(r'blogs', BlogPostViewSet, basename='blog')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'kashmir-route-fares', KashmirRouteFareViewSet, basename='kashmir-route-fare')
router.register(r'inquiries', InquiryViewSet, basename='inquiry')
router.register(r'booking-searches', BookingSearchViewSet, basename='booking-search')
router.register(r'testimonials', TestimonialViewSet, basename='testimonial')
router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'trip-planner/inquiries', TripInquiryViewSet, basename='trip-inquiry')

urlpatterns = [
    path('trip-planner/options/', trip_planner_options, name='trip-planner-options'),
    path('trip-planner/inquiries/', create_trip_inquiry, name='trip-planner-create'),
    path('', include(router.urls)),
]
