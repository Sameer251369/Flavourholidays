from io import BytesIO
from unittest.mock import patch

import cloudinary.exceptions
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from .models import BlogPost, BookingSearch, Destination, Tour


class FailingUploadStorage(FileSystemStorage):
	def _save(self, name, content):
		raise cloudinary.exceptions.Error('Test upload failure')


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
			name='Leh & Ladakh', slug='test-leh-ladakh', description='Ladakh'
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

	def test_ladakh_tour_is_available(self):
		response = self.client.get(reverse('tour-list'))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		ladakh_tour = next(
			(tour for tour in response.data if tour['slug'] == 'leh-ladakh-high-altitude-thrill'),
			None
		)
		self.assertIsNotNone(ladakh_tour)
		self.assertEqual(ladakh_tour['destination_name'], 'Leh & Ladakh')
		self.assertEqual(len(ladakh_tour['checkpoints']), 5)

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


@override_settings(STORAGES={
	'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
	'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class TourAdminSaveTests(TestCase):
	def setUp(self):
		destination = Destination.objects.create(
			name='Kashmir Valley', slug='admin-kashmir', description='Kashmir'
		)
		self.destination = destination
		admin_user = get_user_model().objects.create_superuser(
			username='admin', email='admin@example.com', password='test-password'
		)
		self.client.force_login(admin_user)

	def make_tour_data(self, slug, cover_image_file=None, checkpoint_image_file=None):
		data = {
			'title': 'Admin Test Tour',
			'slug': slug,
			'destination': self.destination.pk,
			'tagline': 'A mountain route',
			'vibe_tag': '#Test',
			'duration_days': 2,
			'duration_nights': 1,
			'starting_price': 1000,
			'difficulty': 'Easy',
			'cover_image_url': 'https://example.com/tour-cover.jpg',
			'gallery_urls': '[]',
			'overview': 'A test route.',
			'inclusions': 'Guide',
			'exclusions': 'Flights',
			'checkpoints-TOTAL_FORMS': '1',
			'checkpoints-INITIAL_FORMS': '0',
			'checkpoints-MIN_NUM_FORMS': '0',
			'checkpoints-MAX_NUM_FORMS': '1000',
			'checkpoints-0-day_number': '1',
			'checkpoints-0-title': 'Arrival',
			'checkpoints-0-location_name': 'Srinagar',
			'checkpoints-0-altitude': '',
			'checkpoints-0-description': 'Arrive and check in.',
			'checkpoints-0-insta_spot': '',
			'checkpoints-0-vibe_highlight': '',
			'checkpoints-0-image_url': '',
			'checkpoints-0-activities': 'Walk',
			'is_featured': 'on',
			'_save': 'Save',
		}
		if cover_image_file:
			data['cover_image_file'] = cover_image_file
		if checkpoint_image_file:
			data['checkpoints-0-image_file'] = checkpoint_image_file
		return data

	def post_tour(self, slug, **images):
		return self.client.post(
			reverse('admin:tours_tour_add'),
			self.make_tour_data(slug, **images),
			follow=True,
		)

	def make_test_image(self, name):
		from PIL import Image

		image_file = BytesIO()
		Image.new('RGB', (1, 1), color='white').save(image_file, format='PNG')
		return SimpleUploadedFile(name, image_file.getvalue(), content_type='image/png')

	def test_tour_and_checkpoint_can_be_saved_in_admin(self):
		response = self.post_tour('admin-test-tour')

		self.assertEqual(response.status_code, 200)
		saved_tour = Tour.objects.get(slug='admin-test-tour')
		self.assertEqual(saved_tour.checkpoints.count(), 1)

	@override_settings(STORAGES={
		'default': {'BACKEND': 'tours.tests.FailingUploadStorage'},
		'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
	})
	def test_tour_and_checkpoint_save_when_image_storage_fails(self):
		with self.assertLogs('tours.admin', level='ERROR'):
			response = self.post_tour(
				'admin-image-failure-tour',
				cover_image_file=self.make_test_image('cover.png'),
				checkpoint_image_file=self.make_test_image('checkpoint.png'),
			)

		self.assertEqual(response.status_code, 200)
		saved_tour = Tour.objects.get(slug='admin-image-failure-tour')
		checkpoint = saved_tour.checkpoints.get()
		self.assertFalse(saved_tour.cover_image_file)
		self.assertFalse(checkpoint.image_file)
		self.assertEqual(saved_tour.cover_image, 'https://example.com/tour-cover.jpg')
		self.assertContains(response, 'could not be uploaded')
		api_response = self.client.get(reverse('tour-list'))
		published_tour = next(
			tour for tour in api_response.data if tour['slug'] == 'admin-image-failure-tour'
		)
		self.assertEqual(published_tour['cover_image'], 'https://example.com/tour-cover.jpg')

	@patch.dict('os.environ', {
		'CLOUDINARY_CLOUD_NAME': 'test-cloud',
		'CLOUDINARY_API_KEY': 'test-key',
		'CLOUDINARY_API_SECRET': 'test-secret',
	})
	@override_settings(
		STORAGES={
			'default': {'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage'},
			'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
		},
		CLOUDINARY_STORAGE={
			'CLOUD_NAME': 'test-cloud',
			'API_KEY': 'test-key',
			'API_SECRET': 'test-secret',
		},
	)
	@patch('cloudinary.uploader.upload')
	def test_cloudinary_uploads_admin_tour_images_and_exposes_them_in_api(self, upload):
		upload.side_effect = [
			{'public_id': 'media/tours/cover'},
			{'public_id': 'media/checkpoints/arrival'},
		]

		response = self.post_tour(
			'admin-cloudinary-tour',
			cover_image_file=self.make_test_image('cover.png'),
			checkpoint_image_file=self.make_test_image('arrival.png'),
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(upload.call_count, 2)
		saved_tour = Tour.objects.get(slug='admin-cloudinary-tour')
		checkpoint = saved_tour.checkpoints.get()
		self.assertIn('res.cloudinary.com/test-cloud/image/upload/', saved_tour.cover_image)
		self.assertIn('media/tours/cover', saved_tour.cover_image)
		self.assertIn('res.cloudinary.com/test-cloud/image/upload/', checkpoint.display_image_url)

		api_response = self.client.get(reverse('tour-list'))
		published_tour = next(
			tour for tour in api_response.data if tour['slug'] == 'admin-cloudinary-tour'
		)
		self.assertEqual(published_tour['cover_image'], saved_tour.cover_image)
		self.assertEqual(published_tour['checkpoints'][0]['image_url'], checkpoint.display_image_url)
