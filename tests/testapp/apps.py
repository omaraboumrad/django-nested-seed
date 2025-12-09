"""Test app configuration."""

from django.apps import AppConfig


class TestAppConfig(AppConfig):
    """Configuration for test app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.testapp"
    label = "testapp"
