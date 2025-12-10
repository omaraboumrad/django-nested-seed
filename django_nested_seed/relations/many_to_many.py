"""ManyToManyField relationship handler."""

from typing import Any, TYPE_CHECKING

from django.db import models
from django.db.models import Field, ManyToManyField

from django_nested_seed.core.registry import ObjectRegistry
from django_nested_seed.relations.base import RelationHandler

if TYPE_CHECKING:
    from django_nested_seed.core.resolver import ModelResolver


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
        resolver: "ModelResolver | None" = None,
    ) -> None:
        """
        Resolve M2M references and set relationships.

        Supports both YAML references ($ref_key) and database lookups (@pk:123, @field:value).

        Args:
            instance: Django model instance
            field_name: M2M field name
            references: List of reference strings (can be $ref or @lookup)
            registry: ObjectRegistry for looking up instances
            resolver: ModelResolver for parsing database lookups (optional)
        """
        resolved_instances = []

        # Get the M2M field to determine target model for database lookups
        try:
            m2m_field_obj = instance._meta.get_field(field_name)
            target_model = m2m_field_obj.related_model
        except Exception:
            target_model = None

        for reference in references:
            # Check if it's a database lookup
            if resolver and resolver.is_db_lookup_pattern(reference):
                if not target_model:
                    raise ValueError(
                        f"Cannot resolve database lookup for M2M field '{field_name}': "
                        f"field not found on model"
                    )
                # Parse and fetch from database
                lookup_params = resolver.parse_db_lookup(reference)
                resolved_instance = registry.get_from_db(target_model, lookup_params)
            else:
                # Regular reference lookup
                resolved_instance = registry.get(reference)

            resolved_instances.append(resolved_instance)

        # Get the M2M field manager and set the relationships
        m2m_field = getattr(instance, field_name)
        m2m_field.set(resolved_instances)
