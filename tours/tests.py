from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import BlogPost, BookingSearch, Destination, Tour

class BookingSearchTests(APITestCase):
	def setUp(self):
		destination = Destination.objects.create(
			name='Kashmir Valley', slug='kashmir-valley', description='Kashmir', cover_image_url='https://example.com/kashmir.jpg'
		)
		self.tour = Tour.objects.create(
			title='Kashmir Tour', slug='kashmir-tour', destination=destination,
			cover_image_url='https://example.com/tour.jpg', overview='Kashmir package'
		)
		self.additional_tour = Tour.objects.create(
			title='Another Kashmir Tour', slug='another-kashmir-tour', destination=destination,
			cover_image_url='https://example.com/another-tour.jpg', overview='Another Kashmir package'
		)
		other_destination = Destination.objects.create(
			name='Leh & Ladakh', slug='leh-ladakh', description='Ladakh'
		)
		other_tour = Tour.objects.create(
			title='Other Tour', slug='other-tour', destination=other_destination,
			cover_image_url='https://example.com/other.jpg', overview='Other package'
		)
		BlogPost.objects.create(
			title='Kashmir Guide', slug='kashmir-guide', cover_image_url='https://example.com/blog.jpg',
			excerpt='Guide', content='Guide content', related_tour=self.tour
		)
		BlogPost.objects.create(
			title='Other Guide', slug='other-guide', cover_image_url='https://example.com/other-blog.jpg',
			excerpt='Guide', content='Other content', related_tour=other_tour
		)

	def test_booking_search_is_saved_and_filters_results(self):
		response = self.client.post(reverse('booking-search-list'), {
			'selected_tour': self.tour.id,
			'check_in': '2026-09-20',
			'check_out': '2026-09-25',
			'people': 3,
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(BookingSearch.objects.count(), 1)
		self.assertEqual(response.data['search']['people'], 3)
		self.assertEqual(
			[tour['id'] for tour in response.data['tours']],
			[self.tour.id, self.additional_tour.id]
		)
		self.assertEqual([blog['title'] for blog in response.data['blogs']], ['Kashmir Guide'])

	def test_booking_search_rejects_checkout_before_checkin(self):
		response = self.client.post(reverse('booking-search-list'), {
			'selected_tour': self.tour.id,
			'check_in': '2026-09-25',
			'check_out': '2026-09-20',
			'people': 2,
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(BookingSearch.objects.count(), 0)
