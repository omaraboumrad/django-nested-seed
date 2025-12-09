"""ManyToManyField relationship handler."""

from typing import Any

from django.db import models
from django.db.models import Field, ManyToManyField

from django_nested_seed.core.registry import ObjectRegistry
from django_nested_seed.relations.base import RelationHandler


class ManyToManyHandler(RelationHandler):
    """Handler for ManyToManyField relationships."""

    def can_handle(self, field: Field) -> bool:
        """
        Check if field is a ManyToManyField.

        Args:
            field: Django model field

        Returns:
            True if field is ManyToManyField
        """
        return isinstance(field, ManyToManyField)

    def prepare_value(self, value: Any, registry: ObjectRegistry) -> Any:
        """
        Not used for M2M - use resolve_and_set instead.

        M2M relationships are handled in a second pass after all objects exist.
        """
        raise NotImplementedError("Use resolve_and_set() for ManyToMany fields")

    def resolve_and_set(
        self,
        instance: models.Model,
        field_name: str,
        references: list[str],
        registry: ObjectRegistry,
    ) -> None:
        """
        Resolve M2M references and set relationships.

        Args:
            instance: Django model instance
            field_name: M2M field name
            references: List of reference strings
            registry: ObjectRegistry for looking up instances
        """
        resolved_instances = []

        for reference in references:
            resolved_instance = registry.get(reference)
            resolved_instances.append(resolved_instance)

        # Get the M2M field manager and set the relationships
        m2m_field = getattr(instance, field_name)
        m2m_field.set(resolved_instances)
