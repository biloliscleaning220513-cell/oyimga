import hashlib
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_list(name, default=''):
    return [x.strip() for x in os.environ.get(name, default).split(',') if x.strip()]


SECRET_KEY = os.environ.get(
    'SECRET_KEY', 'django-insecure-key-for-dev-environment-change-in-production'
)

# Render'da DEBUG avtomatik o'chadi, lokal kompyuterda yoqiq turadi
DEBUG = os.environ.get('DEBUG', '0' if 'RENDER' in os.environ else '1') == '1'

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', '*')

# Saytning to'liq manzili, masalan: https://oyimga.onrender.com
SITE_URL = os.environ.get('SITE_URL', '').rstrip('/')
if not SITE_URL and os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    SITE_URL = 'https://' + os.environ['RENDER_EXTERNAL_HOSTNAME']

CSRF_TRUSTED_ORIGINS = [SITE_URL] if SITE_URL.startswith('http') else []

# ---- Maxfiy admin panel manzili ----
# ADMIN_URL ni o'zingiz o'rnating (masalan: "k7q-boshqaruv-x93m/").
# O'rnatilmasa SECRET_KEY dan tasodifiy ko'rinishdagi manzil hosil qilinadi:
#   python manage.py admin_url  — manzilni ko'rsatadi.
ADMIN_URL = os.environ.get('ADMIN_URL', '').strip('/')
if not ADMIN_URL:
    ADMIN_URL = 'x-' + hashlib.sha256(('admin:' + SECRET_KEY).encode()).hexdigest()[:24]
ADMIN_URL += '/'

# ---- Telegram bot ----
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
# Buyurtmalar keladigan va botdan mahsulot qo'sha oladigan adminlar (Telegram ID lar, vergul bilan)
TELEGRAM_ADMIN_IDS = [int(x) for x in env_list('TELEGRAM_ADMIN_IDS') if x.lstrip('-').isdigit()]
# Yangi mahsulot avtomatik joylanadigan kanal (ixtiyoriy), masalan: @oyimga_kanal
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID', '')
TELEGRAM_WEBHOOK_SECRET = os.environ.get('TELEGRAM_WEBHOOK_SECRET') or (
    hashlib.sha256(('tg:' + TELEGRAM_BOT_TOKEN + SECRET_KEY).encode()).hexdigest()[:32]
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'store',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.site',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Sayt va Telegram bot BITTA bazadan foydalanadi.
# DATABASE_URL berilsa (masalan Render PostgreSQL) o'sha ishlatiladi, aks holda db.sqlite3.
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'uz'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', str(BASE_DIR / 'media'))

DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'loggers': {'store': {'handlers': ['console'], 'level': 'INFO'}},
}
