"""Base relationship handler."""

from abc import ABC, abstractmethod
from typing import Any

from django.db.models import Field

from django_nested_seed.core.registry import ObjectRegistry


class RelationHandler(ABC):
    """Base class for relationship handlers."""

    @abstractmethod
    def can_handle(self, field: Field) -> bool:
        """
        Check if this handler can handle the given field.

        Args:
            field: Django model field

        Returns:
            True if this handler can handle the field
        """
        pass

    @abstractmethod
    def prepare_value(self, value: Any, registry: ObjectRegistry) -> Any:
        """
        Prepare a value for assignment to a relationship field.

        Args:
            value: Raw value (typically a reference string)
            registry: ObjectRegistry for looking up instances

        Returns:
            Prepared value (typically a model instance)
        """
        pass
