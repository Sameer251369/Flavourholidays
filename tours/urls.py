from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DestinationViewSet, TourViewSet, BlogPostViewSet,
    VehicleViewSet, InquiryViewSet, BookingSearchViewSet, TestimonialViewSet, FAQViewSet
)

router = DefaultRouter()
router.register(r'destinations', DestinationViewSet, basename='destination')
router.register(r'tours', TourViewSet, basename='tour')
router.register(r'blogs', BlogPostViewSet, basename='blog')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'inquiries', InquiryViewSet, basename='inquiry')
router.register(r'booking-searches', BookingSearchViewSet, basename='booking-search')
router.register(r'testimonials', TestimonialViewSet, basename='testimonial')
router.register(r'faqs', FAQViewSet, basename='faq')

urlpatterns = [
    path('', include(router.urls)),
]
