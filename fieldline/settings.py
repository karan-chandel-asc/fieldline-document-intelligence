import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(*names, default=""):
    for name in names:
        value = os.getenv(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip().strip('"').strip("'")
    return default


SECRET_KEY = env("SECRET_KEY", default="ui-only-dev-key-replace-in-backend")
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "pages",
    "accounts.apps.AccountsConfig",
    "dashboard.apps.DashboardConfig",
    "documents.apps.DocumentsConfig",
    "schemas.apps.SchemasConfig",
    "exports.apps.ExportsConfig",
    "records.apps.RecordsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

X_FRAME_OPTIONS = "SAMEORIGIN"

ROOT_URLCONF = "fieldline.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "fieldline.context.brand",
            ],
        },
    }
]

WSGI_APPLICATION = "fieldline.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/app/"
LOGOUT_REDIRECT_URL = "/login/"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_PAGINATION_CLASS": "fieldline.pagination.CustomPagination",
    "PAGE_SIZE": 8,
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

GROQ_API_KEY = env("GROQ_API_KEY", "groq_api_key")
GROQ_MODEL = env("GROQ_MODEL", default="openai/gpt-oss-120b")

_celery_dir = BASE_DIR / "tmp" / "celery"
_celery_queue = _celery_dir / "queue"
for _folder in (_celery_queue, _celery_dir / "processed", _celery_dir / "control"):
    _folder.mkdir(parents=True, exist_ok=True)

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="filesystem://")
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "data_folder_in": str(_celery_queue),
    "data_folder_out": str(_celery_queue),
    "processed_folder": str(_celery_dir / "processed"),
    "control_folder": str(_celery_dir / "control"),
}
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="")
CELERY_TASK_IGNORE_RESULT = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_TRACK_STARTED = True
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = env("CELERY_EAGER", default="").lower() in {"1", "true", "yes"}

SITE_URL = env("SITE_URL", default="http://127.0.0.1:8000")
FIVERR_GIG_URL = "https://www.fiverr.com/"
