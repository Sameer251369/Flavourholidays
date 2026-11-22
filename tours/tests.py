from io import BytesIO
from unittest.mock import patch

import cloudinary.exceptions
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from flavour_backend.cloudinary_utils import (
	resolve_cloudinary_credentials,
	sanitize_cloudinary_error,
)
from .models import BlogPost, BookingSearch, Destination, Tour
from .models import (
	PlannerPlace, PlannerStayOption, PlannerTransportOption, PlannerActivity, PlannerAdditionalService,
	PlannerBudgetBand, PlannerTravelStyle, TripInquiry, TripQuotation,
	PlannerSeasonRate,
)


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


class TripPlannerAPITests(APITestCase):
	def setUp(self):
		from django.core.cache import cache
		cache.clear()
		self.place, _ = PlannerPlace.objects.get_or_create(
			slug='test-srinagar', defaults={'name': 'Srinagar', 'region': 'kashmir', 'is_active': True}
		)
		self.stay, _ = PlannerStayOption.objects.get_or_create(
			slug='test-houseboat', defaults={'name': 'Houseboat', 'estimate_per_night': None}
		)
		self.transport, _ = PlannerTransportOption.objects.get_or_create(
			slug='test-suv', defaults={'name': 'SUV', 'estimate_per_day': None}
		)
		self.activity, _ = PlannerActivity.objects.get_or_create(
			slug='test-shikara', defaults={'name': 'Shikara rides', 'estimate_amount': None}
		)
		self.service, _ = PlannerAdditionalService.objects.get_or_create(
			slug='test-airport-transfer', defaults={'name': 'Airport transfer', 'estimate_amount': None}
		)
		self.budget, _ = PlannerBudgetBand.objects.get_or_create(
			slug='test-budget', defaults={'label': '₹10,000–₹20,000'}
		)
		self.style, _ = PlannerTravelStyle.objects.get_or_create(
			slug='test-family', defaults={'name': 'Family vacation'}
		)
		self.payload = {
			'name': 'Test Traveller', 'email': 'traveller@example.com',
			'phone_country_code': '+91', 'phone': '9876543210',
			'departure_date': '2027-06-10', 'return_date': '2027-06-14',
			'adults': 2, 'children': 1, 'infants': 0,
			'destination_slugs': [self.place.slug], 'activity_slugs': [self.activity.slug],
			'additional_service_slugs': [self.service.slug],
			'stay_slug': self.stay.slug, 'transport_slug': self.transport.slug,
			'budget_slug': self.budget.slug, 'budget_scope': 'per_person',
			'travel_style_slug': self.style.slug,
			'food_preferences': '', 'special_requests': '',
			'accessibility_needs': '', 'additional_information': '',
		}

	def test_options_are_public_and_use_backend_catalog(self):
		response = self.client.get(reverse('trip-planner-options'))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(any(item['slug'] == self.place.slug for item in response.data['destinations']))
		self.assertTrue(any(item['slug'] == self.activity.slug for item in response.data['activities']))

	def test_enquiry_saves_preferences_and_returns_reference(self):
		response = self.client.post(reverse('trip-planner-create'), self.payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		inquiry = TripInquiry.objects.get(reference_id=response.data['reference_id'])
		self.assertEqual(inquiry.travelers_total, 3)
		self.assertEqual(inquiry.nights, 4)
		self.assertEqual(list(inquiry.places.all()), [self.place])
		self.assertEqual(list(inquiry.activities.all()), [self.activity])
		self.assertIn('Request a Personalized Quote', response.data['estimate']['message'])

	def test_invalid_dates_are_rejected(self):
		payload = {**self.payload, 'return_date': self.payload['departure_date']}
		response = self.client.post(reverse('trip-planner-create'), payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('return_date', response.data)

	def test_repeat_submit_returns_existing_reference(self):
		first = self.client.post(reverse('trip-planner-create'), self.payload, format='json')
		second = self.client.post(reverse('trip-planner-create'), self.payload, format='json')
		self.assertEqual(first.data['reference_id'], second.data['reference_id'])
		self.assertEqual(TripInquiry.objects.count(), 1)

	def test_configured_prices_include_travellers_trip_days_and_season(self):
		self.stay.estimate_per_night = 4000
		self.stay.save()
		self.transport.estimate_per_day = 2000
		self.transport.save()
		self.activity.estimate_amount = 500
		self.activity.save()
		self.service.estimate_amount = 1200
		self.service.save()
		PlannerSeasonRate.objects.create(
			name='Summer test season', start_month=6, start_day=12,
			end_month=6, end_day=20, multiplier='1.20',
		)
		response = self.client.post(reverse('trip-planner-create'), self.payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data['estimate']['total'], 34440)
		self.assertEqual(response.data['estimate']['season'], 'Summer test season')
		self.assertIn('wa.me/', response.data['whatsapp_url'])

	def test_enquiry_listing_and_retrieval_require_admin(self):
		created = self.client.post(reverse('trip-planner-create'), self.payload, format='json')
		self.assertEqual(self.client.get(reverse('trip-planner-create')).status_code, status.HTTP_403_FORBIDDEN)
		self.assertEqual(self.client.get(f"/api/trip-planner/inquiries/{created.data['reference_id']}/").status_code, status.HTTP_403_FORBIDDEN)
		admin_user = get_user_model().objects.create_superuser(username='planner_admin', email='planner@example.com', password='password123')
		self.client.force_login(admin_user)
		self.assertEqual(self.client.get(reverse('trip-planner-create')).status_code, status.HTTP_200_OK)
		self.assertEqual(self.client.get(f"/api/trip-planner/inquiries/{created.data['reference_id']}/").status_code, status.HTTP_200_OK)

	def test_admin_can_create_quotation(self):
		created = self.client.post(reverse('trip-planner-create'), self.payload, format='json')
		admin_user = get_user_model().objects.create_superuser(username='quote_admin', email='quote@example.com', password='password123')
		self.client.force_login(admin_user)
		response = self.client.post(
			f"/api/trip-planner/inquiries/{created.data['reference_id']}/quotation/",
			{'accommodation_cost': 12000, 'transportation_cost': 6000, 'activities_cost': 1500, 'additional_charges': 500},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data['total_quotation'], 20000)
		self.assertTrue(TripQuotation.objects.filter(inquiry__reference_id=created.data['reference_id']).exists())


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
		with self.assertLogs('flavour_backend.cloudinary_utils', level='ERROR'):
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
		self.assertContains(response, 'Test upload failure')
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
			'SECURE': True,
			'PREFIX': 'media/',
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
			'SECURE': True,
			'PREFIX': 'media/',
		},
	)
	@patch('cloudinary.uploader.upload', side_effect=cloudinary.exceptions.Error('Invalid Signature'))
	def test_cloudinary_network_failure_keeps_previous_urls(self, _upload):
		with self.assertLogs('flavour_backend.cloudinary_utils', level='ERROR'):
			response = self.post_tour(
				'admin-cloudinary-failure-tour',
				cover_image_file=self.make_test_image('cover.png'),
				checkpoint_image_file=self.make_test_image('arrival.png'),
			)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Invalid Signature')
		saved_tour = Tour.objects.get(slug='admin-cloudinary-failure-tour')
		self.assertFalse(saved_tour.cover_image_file)
		self.assertEqual(saved_tour.cover_image, 'https://example.com/tour-cover.jpg')


class CloudinaryCredentialTests(SimpleTestCase):
	def test_resolve_explicit_env_credentials(self):
		credentials, source = resolve_cloudinary_credentials(
			cloud_name='demo-cloud',
			api_key='123456789012345',
			api_secret='abcdefghijklmnopqrstuvwxyz12',
		)
		self.assertEqual(source, 'explicit_env')
		self.assertEqual(credentials['CLOUD_NAME'], 'demo-cloud')

	def test_resolve_cloudinary_url_credentials(self):
		credentials, source = resolve_cloudinary_credentials(
			cloudinary_url='cloudinary://123456789012345:abcdefghijklmnopqrstuvwxyz12@demo-cloud',
		)
		self.assertEqual(source, 'cloudinary_url')
		self.assertEqual(credentials['CLOUD_NAME'], 'demo-cloud')
		self.assertEqual(credentials['API_KEY'], '123456789012345')

	def test_explicit_env_wins_over_url(self):
		credentials, source = resolve_cloudinary_credentials(
			cloud_name='explicit-cloud',
			api_key='111',
			api_secret='secretsecretsecret12',
			cloudinary_url='cloudinary://999:othersecretothersecret@url-cloud',
		)
		self.assertEqual(source, 'explicit_env')
		self.assertEqual(credentials['CLOUD_NAME'], 'explicit-cloud')

	def test_incomplete_credentials_raise(self):
		with self.assertRaises(ValueError):
			resolve_cloudinary_credentials(cloud_name='only-name')

	def test_sanitize_redacts_long_tokens(self):
		exc = cloudinary.exceptions.Error('Invalid api_key abcdefghijklmnopqrstuvwxyz012345')
		safe = sanitize_cloudinary_error(exc)
		self.assertIn('Error', safe)
		self.assertNotIn('abcdefghijklmnopqrstuvwxyz012345', safe)
		self.assertIn('[redacted]', safe)


@override_settings(STORAGES={
	'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
	'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class BlogPostSEOTests(TestCase):
	def setUp(self):
		self.destination = Destination.objects.create(
			name='Kashmir Valley', slug='seo-kashmir', description='Kashmir'
		)
		self.tour = Tour.objects.create(
			title='Kashmir Winter Tour', slug='kashmir-winter-tour', destination=self.destination,
			overview='Winter tour package'
		)

	def test_blog_post_seo_fallbacks(self):
		blog = BlogPost.objects.create(
			title='Kashmir Snow Guide',
			slug='kashmir-snow-guide',
			excerpt='A brief excerpt about Kashmir snow.',
			content='Full guide content here.',
			related_tour=self.tour
		)
		self.assertEqual(blog.effective_seo_title, 'Kashmir Snow Guide | Flavour Holidays')
		self.assertEqual(blog.effective_meta_description, 'A brief excerpt about Kashmir snow.')
		self.assertEqual(blog.effective_canonical_url, 'https://www.flavourholidays.com/blog/kashmir-snow-guide/')
		self.assertEqual(blog.effective_image_alt, 'Kashmir Snow Guide')
		self.assertTrue(blog.allow_indexing)

	def test_blog_post_explicit_seo_fields(self):
		blog = BlogPost.objects.create(
			title='Kashmir in Winter 2026–27: Weather, Snowfall & Travel Guide',
			slug='kashmir-in-winter-2026',
			seo_title='Kashmir in Winter 2026–27: Travel Guide | Flavour Holidays',
			meta_description='Plan your Kashmir winter trip with our complete guide.',
			meta_keywords='kashmir in winter, kashmir snowfall guide',
			canonical_url='https://www.flavourholidays.com/blog/kashmir-in-winter-2026/',
			image_alt='Snow-covered mountains in Gulmarg, Kashmir',
			allow_indexing=True,
			related_tour=self.tour
		)
		self.assertEqual(blog.effective_seo_title, 'Kashmir in Winter 2026–27: Travel Guide | Flavour Holidays')
		self.assertEqual(blog.effective_meta_description, 'Plan your Kashmir winter trip with our complete guide.')
		self.assertEqual(blog.effective_canonical_url, 'https://www.flavourholidays.com/blog/kashmir-in-winter-2026/')
		self.assertEqual(blog.effective_image_alt, 'Snow-covered mountains in Gulmarg, Kashmir')

	def test_blog_post_api_serializer(self):
		from tours.serializers import BlogPostSerializer
		blog = BlogPost.objects.create(
			title='API Test Blog',
			slug='api-test-blog',
			meta_keywords='test, api',
			related_tour=self.tour
		)
		serializer = BlogPostSerializer(blog)
		data = serializer.data
		self.assertEqual(data['seo_title'], 'API Test Blog | Flavour Holidays')
		self.assertEqual(data['canonical_url'], 'https://www.flavourholidays.com/blog/api-test-blog/')
		self.assertEqual(data['meta_keywords'], 'test, api')
		self.assertTrue(data['allow_indexing'])

	def test_blog_post_admin_save(self):
		admin_user = get_user_model().objects.create_superuser(
			username='blog_admin', email='blog_admin@example.com', password='password123'
		)
		self.client.force_login(admin_user)
		response = self.client.post(reverse('admin:tours_blogpost_add'), {
			'title': 'Admin Added Blog',
			'slug': 'admin-added-blog',
			'category': 'Guide',
			'read_time': '5 min read',
			'author': 'Flavour Squad',
			'vibe_tag': '#Winter',
			'related_tour': self.tour.pk,
			'seo_title': 'Admin Added Blog | Flavour Holidays',
			'meta_description': 'A meta description for SEO testing.',
			'meta_keywords': 'kashmir, winter',
			'canonical_url': 'https://www.flavourholidays.com/blog/admin-added-blog/',
			'image_alt': 'Admin blog alt text',
			'allow_indexing': 'on',
			'excerpt': 'Admin excerpt',
			'content': 'Admin full content',
			'_save': 'Save'
		}, follow=True)
		self.assertEqual(response.status_code, 200)
		saved = BlogPost.objects.get(slug='admin-added-blog')
		self.assertEqual(saved.seo_title, 'Admin Added Blog | Flavour Holidays')
		self.assertEqual(saved.image_alt, 'Admin blog alt text')
		self.assertTrue(saved.allow_indexing)

