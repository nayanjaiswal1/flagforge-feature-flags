SECRET_KEY = "django-insecure-test-key"  # pragma: allowlist secret
DEBUG = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "flagforge.contrib.django",
]
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "flagforge.contrib.django.middleware.RequestCacheMiddleware",
]
ROOT_URLCONF = "tests.urls"
FLAGFORGE_TENANCY_MODE = "column"
USE_TZ = True
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
]
