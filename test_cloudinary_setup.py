import os
import django

os.environ['CLOUDINARY_URL'] = 'cloudinary://123456789:abcdefghijk@mytestcloud'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flavour_backend.settings')
django.setup()

import cloudinary
from cloudinary_storage import storage

print('cloudinary.config().cloud_name:', cloudinary.config().cloud_name)
print('cloudinary.config().api_key:', cloudinary.config().api_key)
print('cloudinary.config().api_secret:', cloudinary.config().api_secret)
print('cloudinary.config().secure:', cloudinary.config().secure)

s = storage.MediaCloudinaryStorage()
print('Storage url for test:', s.url('checkpoints/day1.jpg'))
