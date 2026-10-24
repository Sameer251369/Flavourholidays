"""Verify Cloudinary credentials without printing secrets."""

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

import cloudinary
import cloudinary.api


class Command(BaseCommand):
    help = (
        'Verify Cloudinary is configured and credentials can authenticate. '
        'Never prints API secrets.'
    )

    def handle(self, *args, **options):
        source = getattr(settings, 'CLOUDINARY_CONFIG_SOURCE', 'unknown')
        cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', '') or cloudinary.config().cloud_name
        storage_backend = default_storage.__class__.__module__ + '.' + default_storage.__class__.__name__

        self.stdout.write(f'Config source: {source}')
        self.stdout.write(f'Cloud name: {cloud_name or "(missing)"}')
        self.stdout.write(f'API key set: {bool(getattr(settings, "CLOUDINARY_API_KEY", "") or cloudinary.config().api_key)}')
        self.stdout.write(f'API secret set: {bool(getattr(settings, "CLOUDINARY_API_SECRET", "") or cloudinary.config().api_secret)}')
        self.stdout.write(f'Default storage: {storage_backend}')

        if not cloud_name or not (cloudinary.config().api_key and cloudinary.config().api_secret):
            raise CommandError(
                'Cloudinary credentials are missing. Set CLOUDINARY_URL or '
                'CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET.'
            )

        if 'MediaCloudinaryStorage' not in storage_backend:
            raise CommandError(
                'Default storage is not MediaCloudinaryStorage. '
                'Uploads will not go to Cloudinary.'
            )

        try:
            # ping / usage is a lightweight authenticated Admin API call
            cloudinary.api.ping()
        except Exception as exc:
            raise CommandError(
                f'Cloudinary authentication failed ({type(exc).__name__}). '
                'Check that the cloud name, API key, and API secret belong to the '
                'same Cloudinary product environment and were pasted without quotes/spaces.'
            ) from exc

        self.stdout.write(self.style.SUCCESS('Cloudinary credentials authenticated successfully.'))
