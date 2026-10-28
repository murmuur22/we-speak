"""Environment-driven settings; development must be explicitly enabled."""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get('WE_SPEAK_DEV') == '1'
SECRET_KEY = os.environ.get('WE_SPEAK_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('Set WE_SPEAK_SECRET_KEY, or WE_SPEAK_DEV=1 for loopback development.')
    SECRET_KEY = get_random_secret_key()
if not DEBUG and len(SECRET_KEY) < 50:
    raise ImproperlyConfigured('WE_SPEAK_SECRET_KEY must contain at least 50 random characters.')
ALLOWED_HOSTS = os.environ.get('WE_SPEAK_HOSTS', 'localhost,127.0.0.1,[::1]').split(',')
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'forum',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'forum.middleware.PrivacyHeadersMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'forum.middleware.WriteLimitMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [],
    'APP_DIRS': True, 'OPTIONS': {'context_processors': [
        'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATA_DIR = Path(os.environ.get('WE_SPEAK_DATA', BASE_DIR / 'data'))
DATA_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
FILE_UPLOAD_TEMP_DIR = DATA_DIR / 'upload-tmp'
FILE_UPLOAD_TEMP_DIR.mkdir(exist_ok=True, mode=0o700)
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': DATA_DIR / 'forum.sqlite3', 'OPTIONS': {'timeout': 10, 'transaction_mode': 'IMMEDIATE'}}}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static-built'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_REDIRECT_EXEMPT = [r'^healthz/$']
# Enable ONLY when the application is reachable exclusively through a proxy
# that replaces this header. The supplied Compose topology provides that boundary.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if os.environ.get('WE_SPEAK_TRUST_PROXY') == '1' else None
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
DATA_UPLOAD_MAX_MEMORY_SIZE = 65536
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
