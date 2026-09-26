import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# SECURITY
# =========================================================

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-flavour-holidays-genz-redesign-key-2026'
)

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')

allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', '*')
ALLOWED_HOSTS = [
    host.strip()
    for host in allowed_hosts_env.split(',')
    if host.strip()
]


# =========================================================
# INSTALLED APPS
# =========================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'corsheaders',

    # Local apps
    'tours',
]


# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =========================================================
# URLS / TEMPLATES
# =========================================================

ROOT_URLCONF = 'flavour_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'flavour_backend.wsgi.application'


# =========================================================
# DATABASE
# =========================================================
# Local:
#     SQLite is used if DATABASE_URL does not exist.
#
# Production:
#     Neon PostgreSQL is used through DATABASE_URL.
#
# IMPORTANT:
# Put your Neon DATABASE_URL in Render Environment Variables.
# Do NOT hardcode the password here.
# =========================================================

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# =========================================================
# PASSWORD VALIDATION
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'
    },
]


# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# =========================================================
# STATIC FILES
# =========================================================

STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },

    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =========================================================
# MEDIA FILES
# =========================================================

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


# =========================================================
# CLOUDINARY
# =========================================================

CLOUDINARY_CLOUD_NAME = os.environ.get(
    'CLOUDINARY_CLOUD_NAME',
    ''
)

CLOUDINARY_API_KEY = os.environ.get(
    'CLOUDINARY_API_KEY',
    ''
)

CLOUDINARY_API_SECRET = os.environ.get(
    'CLOUDINARY_API_SECRET',
    ''
)

CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')
cloudinary_is_configured = bool(CLOUDINARY_URL) or all((
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
))

if cloudinary_is_configured:

    if 'cloudinary_storage' not in INSTALLED_APPS:
        INSTALLED_APPS.insert(0, 'cloudinary_storage')

    if 'cloudinary' not in INSTALLED_APPS:
        INSTALLED_APPS.append('cloudinary')

    if all((CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET)):
        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
            'API_KEY': CLOUDINARY_API_KEY,
            'API_SECRET': CLOUDINARY_API_SECRET,
        }

    STORAGES['default'] = {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    }


# =========================================================
# CORS
# =========================================================

cors_origins_env = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    ''
)

if cors_origins_env:

    CORS_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in cors_origins_env.split(',')
        if origin.strip()
    ]

    CORS_ALLOW_ALL_ORIGINS = False

else:
    CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True


# =========================================================
# CSRF
# =========================================================

csrf_origins_env = os.environ.get(
    'CSRF_TRUSTED_ORIGINS',
    ''
)

if csrf_origins_env:

    CSRF_TRUSTED_ORIGINS = [
        origin.strip()
        for origin in csrf_origins_env.split(',')
        if origin.strip()
    ]