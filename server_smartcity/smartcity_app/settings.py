import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-smartcity-super-secret-key'
DEBUG = True

# Izinkan server diakses dari host mana pun di internet saat deploy
ALLOWED_HOSTS = ['*']

# Pendaftaran Aplikasi Utama & Pihak Ketiga (Lab 2, 3, 6, 9, 11, 14)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Library Eksternal
    'rest_framework',
    'drf_spectacular',
    'django_scalar',
    'rest_framework_simplejwt',
    'corsheaders',
    
    # Aplikasi Proyek Smart City
    'main_app',
    'usermanagement',
]

# Middleware (CorsMiddleware diletakkan di paling atas)
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smartcity_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'smartcity_app.wsgi.application'

# Koneksi Database Kredensial Asli Kelompok mhs08
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'db_mhs08',        
        'USER': 'mhs08',          
        'PASSWORD': 'mhs08', 
        'HOST': '127.0.0.1',      
        'PORT': '5432',           
    }
}

# Deklarasi Custom User Model (Lab 6)
AUTH_USER_MODEL = 'usermanagement.CustomUser'

LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# Manajemen Durasi Sesi Token JWT (Lab 10)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Mengizinkan akses lintas origin agar frontend SPA tidak CORS Error
CORS_ALLOW_ALL_ORIGINS = True

# Lokasi folder untuk mengumpulkan file statis DRF saat deployment
STATIC_ROOT = BASE_DIR / 'staticfiles'

CSRF_TRUSTED_ORIGINS = [
    'http://103.151.63.87:8008',
    'http://103.151.63.87',
    'https://iet-polinela.github.io'
]

# Metadata OpenAPI-based Documentation Lab 14[cite: 1]
# Metadata OpenAPI-based Documentation Lab 14
SPECTACULAR_SETTINGS = {
    'TITLE': 'Smart City Portal API - Pesawaran',
    'DESCRIPTION': 'Dokumentasi REST API resmi untuk Portal Pelaporan Laporan Warga',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}