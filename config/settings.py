import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DEBUG", "0") == "1"

_secret = os.environ.get("SECRET_KEY", "")
if not _secret:
    if not DEBUG:
        raise ImproperlyConfigured("SECRET_KEY environment variable is required when DEBUG=False")
    from django.core.management.utils import get_random_secret_key

    _secret = get_random_secret_key()
SECRET_KEY = _secret

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost").split(",")

CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "http://localhost").split(",")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "core",
    "accounts",
    "books",
    "inventory",
    "loans",
    "requests_app",
    "audit",
    "dashboard",
    "freedom_wall",
    "announcements",
    "demo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "core.middleware.LoginRequiredMiddleware",
    "core.middleware.MustChangePasswordMiddleware",
    "demo.middleware.DemoReadOnlyMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", ""),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", 600)),
        "OPTIONS": {"sslmode": os.environ.get("DB_SSLMODE", "prefer")},
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"),
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "accounts.backends.LRNAuthenticationBackend",
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "accounts.validators.MinimumLengthValidator"},
    {"NAME": "accounts.validators.UppercaseValidator"},
    {"NAME": "accounts.validators.LowercaseValidator"},
    {"NAME": "accounts.validators.NumberValidator"},
    {"NAME": "accounts.validators.SpecialCharacterValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "accounts:login"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Manila"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "core" / "static",
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

RATELIMIT_USE_CACHE = "default"
RATELIMIT_ENABLE = not DEBUG

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
_broker_url = os.environ.get("CELERY_BROKER_URL", "")
if not _broker_url:
    _base = REDIS_URL.rsplit("/", 1)[0]
    _broker_url = f"{_base}/1"
CELERY_BROKER_URL = _broker_url
_result_backend = os.environ.get("CELERY_RESULT_BACKEND", "")
if not _result_backend:
    _base = REDIS_URL.rsplit("/", 1)[0]
    _result_backend = f"{_base}/2"
CELERY_RESULT_BACKEND = _result_backend
CELERY_TIMEZONE = "Asia/Manila"
CELERY_ENABLE_UTC = False

SESSION_COOKIE_AGE = 86400
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

ADMIN_LRN = os.environ.get("ADMIN_LRN", "ADMIN")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Booklat@Admin2026!")

DEMO_MODE = os.environ.get("DEMO_MODE", "0") == "1"

MAX_CSV_UPLOAD_SIZE = int(os.environ.get("MAX_CSV_UPLOAD_SIZE", 5 * 1024 * 1024))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "WARNING"),
    },
}