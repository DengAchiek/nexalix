import os
from pathlib import Path

try:
    import dj_database_url
except ImportError:  # pragma: no cover - optional in local dev until prod deps are installed
    dj_database_url = None

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-local-dev-only-change-me")

DEBUG = os.getenv("DEBUG", "True").lower() in {"1", "true", "yes", "on"}

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

# --------------------
# APPLICATIONS
# --------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "nexalix_app.apps.NexalixAppConfig",
]

# --------------------
# MIDDLEWARE
# --------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if not DEBUG:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "nexalix_site.urls"

# --------------------
# TEMPLATES
# --------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # ✅ allows project-level templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = "nexalix_site.wsgi.application"

# --------------------
# DATABASE
# --------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and dj_database_url:
    DATABASES["default"] = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=not DEBUG,
    )

# --------------------
# CACHE (Redis if available)
# --------------------
REDIS_URL = os.getenv("REDIS_URL", "").strip()
CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "TIMEOUT": CACHE_DEFAULT_TIMEOUT,
            "OPTIONS": {
                "socket_connect_timeout": 3,
                "socket_timeout": 3,
                "retry_on_timeout": True,
            },
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "nexalix-local-cache",
            "TIMEOUT": CACHE_DEFAULT_TIMEOUT,
        }
    }

# --------------------
# INTERNATIONALIZATION
# --------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "Africa/Nairobi")
USE_I18N = True
USE_TZ = True

# --------------------
# STATIC & MEDIA
# --------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "nexalix_app" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "").strip()
use_cloudinary_media_raw = os.getenv("USE_CLOUDINARY_MEDIA")
if use_cloudinary_media_raw is None:
    # Auto-enable Cloudinary when CLOUDINARY_URL is present.
    USE_CLOUDINARY_MEDIA = bool(CLOUDINARY_URL)
else:
    USE_CLOUDINARY_MEDIA = use_cloudinary_media_raw.lower() in {"1", "true", "yes", "on"}

# Django 5+/6 storage settings.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

if USE_CLOUDINARY_MEDIA and CLOUDINARY_URL:
    # Use Cloudinary for uploaded media files in production.
    INSTALLED_APPS += ["cloudinary_storage", "cloudinary"]
    STORAGES["default"] = {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    }
    CLOUDINARY_STORAGE = {
        "SECURE": True,
    }

# --------------------
# EMAIL (REAL TIME SMTP)
# --------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in {"1", "true", "yes", "on"}

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    f"Nexalix Technologies <{EMAIL_HOST_USER or 'noreply@nexalix.com'}>",
)

# Primary inbox for contact form notifications.
CONTACT_NOTIFICATION_EMAIL = os.getenv("CONTACT_NOTIFICATION_EMAIL", "dachiek4@gmail.com").strip()

ADMIN_EMAILS = [
    email.strip()
    for email in os.getenv("ADMIN_EMAILS", CONTACT_NOTIFICATION_EMAIL).split(",")
    if email.strip()
]

if CONTACT_NOTIFICATION_EMAIL and CONTACT_NOTIFICATION_EMAIL not in ADMIN_EMAILS:
    ADMIN_EMAILS.append(CONTACT_NOTIFICATION_EMAIL)

SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")

CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", EMAIL_HOST_USER or CONTACT_NOTIFICATION_EMAIL)

# --------------------
# CHATBOT SETTINGS
# --------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip()
OPENAI_CHAT_TEMPERATURE = float(os.getenv("OPENAI_CHAT_TEMPERATURE", "0.3"))
OPENAI_CHAT_MAX_TOKENS = int(os.getenv("OPENAI_CHAT_MAX_TOKENS", "500"))
CHATBOT_SESSION_HISTORY_LIMIT = int(os.getenv("CHATBOT_SESSION_HISTORY_LIMIT", "16"))

CHATBOT_RATE_LIMIT_COUNT = int(os.getenv("CHATBOT_RATE_LIMIT_COUNT", "20"))
CHATBOT_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("CHATBOT_RATE_LIMIT_WINDOW_SECONDS", "600"))

CHATBOT_LEAD_RATE_LIMIT_COUNT = int(os.getenv("CHATBOT_LEAD_RATE_LIMIT_COUNT", "6"))
CHATBOT_LEAD_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("CHATBOT_LEAD_RATE_LIMIT_WINDOW_SECONDS", "600"))

CHATBOT_WIDGET_ENABLED = os.getenv("CHATBOT_WIDGET_ENABLED", "True").lower() in {"1", "true", "yes", "on"}
CHATBOT_WHATSAPP_URL = os.getenv("CHATBOT_WHATSAPP_URL", "https://wa.me/254768774232")

if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() in {"1", "true", "yes", "on"}
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    STORAGES["staticfiles"] = {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    }

# --------------------
# LOGGING
# --------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "loggers": {
        "nexalix_app": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        }
    },
}
