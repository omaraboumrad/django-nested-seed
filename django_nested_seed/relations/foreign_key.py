"""ForeignKey relationship handler."""

from typing import Any

from django.db.models import Field, ForeignKey

from django_nested_seed.core.registry import ObjectRegistry
from django_nested_seed.relations.base import RelationHandler


class ForeignKeyHandler(RelationHandler):
    """Handler for ForeignKey relationships."""

    def can_handle(self, field: Field) -> bool:
        """
        Check if field is a ForeignKey.

        Args:
            field: Django model field

        Returns:
            True if field is ForeignKey
        """
        return isinstance(field, ForeignKey)

    def prepare_value(self, value: Any, registry: ObjectRegistry) -> Any:
        """
        Resolve ForeignKey reference to instance.

        Args:
            value: Reference string (e.g., "accounts.users.admin")
            registry: ObjectRegistry for looking up instances

        Returns:
            Django model instance
        """
        if isinstance(value, str):
            # Assume it's a reference string
            return registry.get(value)

        # If not a string, return as-is (might be already resolved)
        return value
