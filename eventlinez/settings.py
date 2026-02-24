import os
import logging
import dj_database_url
from dotenv import load_dotenv

# ----- Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

logger = logging.getLogger(__name__)

# ----- Helpers
def env_bool(key, default=False):
    v = os.getenv(key)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")

# ----- Core
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "chave-padrao-segura")
DEBUG = os.getenv("DEBUG", "False").strip().lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")  # for dev, "*" is fine

# Required in Django 4+ with DEBUG=False so the admin login CSRF check passes
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "https://eventlinez.com,https://www.eventlinez.com,http://localhost:8000"
).split(",")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_placeholder")
STRIPE_WEBHOOK_SECRET = "whsec_UncYtClVKoVzrioZyCT3vouPDASAztau"

# App Host URL for QR codes and external links
APP_HOST = os.getenv("APP_HOST", "http://localhost:8000")


# ----- Email (env-driven; defaults suitable for SendGrid SMTP)
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@eventlinez.com")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

# ----- Database (PostgreSQL only)
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=int(os.getenv("DB_CONN_MAX_AGE", "60")),
        )
    }
else:
    # Detect if running in Docker
    IN_DOCKER = os.path.exists('/.dockerenv') or os.environ.get('IN_DOCKER', False)

    # Set default host based on environment
    if IN_DOCKER:
        default_host = "db"  # Docker service name
    else:
        default_host = "localhost"  # Local development

    # Default to PostgreSQL
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "eventlinez"),
            "USER": os.getenv("POSTGRES_USER", "eventlinez"), 
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "Texera123@"),
            "HOST": os.getenv("POSTGRES_HOST", default_host),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }

# Optional SSH tunnel (OFF in Docker by default)
SSH_TUNNEL_ENABLE = env_bool("SSH_TUNNEL_ENABLE", False)
if SSH_TUNNEL_ENABLE:
    try:
        from sshtunnel import SSHTunnelForwarder
        SSH_TUNNEL = SSHTunnelForwarder(
            (os.getenv("SSH_HOST"), int(os.getenv("SSH_PORT", "22"))),
            ssh_username=os.getenv("SSH_USER"),
            ssh_password=os.getenv("SSH_PASSWORD"),
            remote_bind_address=(os.getenv("REMOTE_DB_HOST", "127.0.0.1"),
                                 int(os.getenv("REMOTE_DB_PORT", "5432"))),
        )
        SSH_TUNNEL.start()
        logger.info("SSH tunnel started on local port %s", getattr(SSH_TUNNEL, "local_bind_port", "?"))
        # Only override host/port if we actually started a tunnel
        DATABASES["default"]["HOST"] = "127.0.0.1"
        DATABASES["default"]["PORT"] = str(SSH_TUNNEL.local_bind_port)
    except Exception as e:
        logger.exception("SSH tunnel failed to start; continuing without it: %s", e)

# ----- Apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "imagekit",
    "crispy_forms",
    "bootstrap_datepicker_plus",
    "ckeditor",
    "address",
    "customer",
    "promoter",
    "event",
    "shop",
    "cart",
    "order",
    "ticket",
    "rest_framework",
    "account",
    "rest_framework.authtoken",
    "eventlinez",
]

# Conditionally add crispy_bootstrap4 if available
try:
    import crispy_bootstrap4
    INSTALLED_APPS.append("crispy_bootstrap4")
except ImportError:
    # crispy_bootstrap4 not available, using built-in bootstrap4 support in django-crispy-forms
    pass

# Crispy Forms Configuration
# Handle different versions based on available packages
try:
    import crispy_bootstrap4
    CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
    CRISPY_TEMPLATE_PACK = "bootstrap4"
except ImportError:
    # Fallback for Python 3.6 or when crispy-bootstrap4 is not available
    # Use built-in bootstrap4 support in older django-crispy-forms versions
    CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
    CRISPY_TEMPLATE_PACK = "bootstrap4"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Add WhiteNoise for static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "eventlinez.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "shop.context_processors.menu_links",
                "cart.context_processors.counter",
            ],
        },
    },
]

WSGI_APPLICATION = "eventlinez.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Los_Angeles"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
}

# File upload settings for larger photo album uploads (200MB max)
FILE_UPLOAD_MAX_MEMORY_SIZE = 200 * 1024 * 1024  # 200MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 200 * 1024 * 1024  # 200MB

# Additional upload settings for better handling of large files
FILE_UPLOAD_TEMP_DIR = os.path.join(BASE_DIR, 'tmp', 'uploads')
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Ensure temp upload directory exists
os.makedirs(FILE_UPLOAD_TEMP_DIR, exist_ok=True)

# Feature flags / misc
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
EVENTLINEZ_FEE = float(os.getenv("EVENTLINEZ_FEE", "0.12"))

# Cache configuration for rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 10000,
        }
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'handlers': {
        'console': { 'class': 'logging.StreamHandler' }
    },
    'loggers': {
        '': { 'handlers': ['console'], 'level': 'INFO' }
    }
}

# Cart Rate Limiting Configuration
CART_RATE_LIMITS = {
    'cart_add': {'requests': 30, 'window': 300},      # 30 requests per 5 minutes
    'cart_checkout': {'requests': 5, 'window': 300},   # 5 checkouts per 5 minutes  
    'promo_apply': {'requests': 10, 'window': 300},    # 10 promo attempts per 5 minutes
    'quantity_change': {'requests': 50, 'window': 300}, # 50 quantity changes per 5 minutes
    'item_remove': {'requests': 20, 'window': 300},    # 20 item removals per 5 minutes
}

# Google reCAPTCHA settings (optional - for contact form spam protection)
# Using reCAPTCHA Enterprise API
RECAPTCHA_PUBLIC_KEY = os.getenv("RECAPTCHA_PUBLIC_KEY", "")
RECAPTCHA_PRIVATE_KEY = os.getenv("RECAPTCHA_PRIVATE_KEY", "")
RECAPTCHA_PROJECT_ID = os.getenv("RECAPTCHA_PROJECT_ID", "")
# Score threshold for reCAPTCHA validation (0.0 - 1.0)
RECAPTCHA_REQUIRED_SCORE = 0.5


def env_bool(key, default=False):
    v = os.getenv(key)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")

ENV = os.getenv("ENV", "dev")
PROD = env_bool("PROD", ENV in ("prod", "production"))


# Local overrides (optional)
try:
    from local_settings import *  # noqa
except ImportError:
    pass

# Sentry init (optional)
try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True,
    )
except ImportError:
    pass
