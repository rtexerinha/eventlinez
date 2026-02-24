# local_settings.example.py
# ------------------------------------------------------------
# Copy this file to local_settings.py on the production server
# at /app/eventlinez/local_settings.py and fill in real values.
# This file is safe to commit - it contains NO real secrets.
# ------------------------------------------------------------

print("Importing local settings")

# --- Stripe (use live keys on production) ---
STRIPE_PUBLISHABLE_KEY = 'pk_live_YOUR_KEY_HERE'
STRIPE_SECRET_KEY = 'sk_live_YOUR_KEY_HERE'

# --- Email ---
CRISPY_TEMPLATE_PACK = 'bootstrap4'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = '587'
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'SG.YOUR_SENDGRID_KEY_HERE'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "noreply@eventlinez.com"

# --- Paths ---
MEDIA_ROOT = '/app/media'
STATIC_ROOT = '/app/static'

# --- Hosts (must include all domains the server responds to) ---
ALLOWED_HOSTS = ['store.calisamba.com', 'eventlinez.com', 'www.eventlinez.com', '50.116.31.214']

# --- CSRF (required in Django 4+ with DEBUG=False for admin login to work) ---
CSRF_TRUSTED_ORIGINS = ['https://eventlinez.com', 'https://www.eventlinez.com']

# --- Database ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'eventlinez',
        'USER': 'eventlinez',
        'PASSWORD': 'YOUR_DB_PASSWORD_HERE',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# --- Misc ---
DEBUG = False
TIME_ZONE = 'America/Los_Angeles'
SENTRY_DSN = "https://YOUR_SENTRY_DSN_HERE"
EVENTLINEZ_FEE = 0.12
APP_HOST = 'https://www.eventlinez.com'
