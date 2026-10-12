import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flavour_backend.settings')
django.setup()

from django.conf import settings
from django.core.files.storage import default_storage

print('DEBUG:', settings.DEBUG)
print('STORAGES:', settings.STORAGES)
print('default_storage class:', default_storage.__class__)
print('CLOUDINARY_URL env:', bool(os.environ.get('CLOUDINARY_URL')))
print('CLOUDINARY_CLOUD_NAME env:', os.environ.get('CLOUDINARY_CLOUD_NAME'))
print('CLOUDINARY_STORAGE setting:', getattr(settings, 'CLOUDINARY_STORAGE', None))
