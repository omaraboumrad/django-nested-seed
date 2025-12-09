"""Django settings for test app."""

SECRET_KEY = "test-secret-key"

DEBUG = True

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "tests.testapp",
    "django_nested_seed",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

USE_TZ = True

# No configuration needed! Auto-discovery handles everything.
# Nested relationships are detected automatically using Django's introspection.
