import os
import logging
import dj_database_url

logger = logging.getLogger(__name__)

# ----- Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_placeholder")

# App Host URL for QR codes and external links
APP_HOST = os.getenv("APP_HOST", "http://localhost:8000")


# ----- Database (container-native)
USE_SQLITE = env_bool("USE_SQLITE", False)

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and not USE_SQLITE:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=int(os.getenv("DB_CONN_MAX_AGE", "60")),
        )
    }
elif USE_SQLITE:
    # SQLite configuration when explicitly requested
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
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

# Feature flags / misc
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
EVENTLINEZ_FEE = float(os.getenv("EVENTLINEZ_FEE", "0.12"))


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
