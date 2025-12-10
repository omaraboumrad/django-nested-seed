"""Object registry and descriptors for tracking seed data."""

from dataclasses import dataclass, field
from typing import Any

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import models

from django_nested_seed.core.exceptions import ReferenceError


@dataclass
class ObjectDescriptor:
    """
    Descriptor for a single object to be created.

    Attributes:
        identity: Dotted path identity (e.g., "accounts.users.admin")
        app_label: Django app label
        collection_name: Collection name from YAML
        object_key: Object key within collection
        model_class: Django model class
        fields: Field values (primitives + unresolved FK/O2O references)
        m2m_fields: ManyToMany field values (lists of reference strings or identities)
        m2m_inline_children: Dict of M2M field name -> list of inline child descriptors
        nested_children: List of nested child descriptors
        parent_descriptor: Parent descriptor (for nested objects)
        parent_field_name: Field name that connects child to parent
        has_explicit_ref: Whether object_key came from explicit $ref (not auto-generated)
    """

    identity: str
    app_label: str
    collection_name: str
    object_key: str
    model_class: type[models.Model]
    fields: dict[str, Any] = field(default_factory=dict)
    m2m_fields: dict[str, list[str]] = field(default_factory=dict)
    m2m_inline_children: dict[str, list["ObjectDescriptor"]] = field(default_factory=dict)
    nested_children: list["ObjectDescriptor"] = field(default_factory=list)
    parent_descriptor: "ObjectDescriptor | None" = None
    parent_field_name: str | None = None
    has_explicit_ref: bool = False

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"ObjectDescriptor(identity='{self.identity}', "
            f"model={self.model_class.__name__}, "
            f"fields={len(self.fields)}, "
            f"m2m={len(self.m2m_fields)}, "
            f"children={len(self.nested_children)})"
        )


class ObjectRegistry:
    """
    Registry for tracking created model instances by identity.

    Maps dotted path identity (e.g., "accounts.users.admin") to Django model instance.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._registry: dict[str, models.Model] = {}
        self._ref_key_index: dict[str, str] = {}  # Maps ref_key -> full identity
        self._creation_order: list[str] = []
        self._db_lookup_cache: dict[str, models.Model] = {}  # Cache for database lookups

    def register(self, identity: str, instance: models.Model, ref_key: str | None = None) -> None:
        """
        Register a created instance.

        Args:
            identity: Dotted path identity
            instance: Django model instance
            ref_key: Optional reference key for $ref_key lookups

        Raises:
            ValueError: If identity already registered or ref_key conflicts
        """
        if identity in self._registry:
            raise ValueError(f"Identity '{identity}' already registered")

        self._registry[identity] = instance
        self._creation_order.append(identity)

        # Register ref_key index if provided
        if ref_key:
            if ref_key in self._ref_key_index:
                existing_identity = self._ref_key_index[ref_key]
                raise ValueError(
                    f"Reference key '{ref_key}' already used by '{existing_identity}'. "
                    f"Reference keys must be unique across all models."
                )
            self._ref_key_index[ref_key] = identity

    def get(self, identity_or_ref: str) -> models.Model:
        """
        Get instance by identity or $ref_key.

        Args:
            identity_or_ref: Dotted path identity or $ref_key

        Returns:
            Django model instance

        Raises:
            ReferenceError: If identity not found
        """
        # Try direct identity lookup first
        if identity_or_ref in self._registry:
            return self._registry[identity_or_ref]

        # If it starts with $, try ref_key lookup
        if identity_or_ref.startswith("$"):
            ref_key = identity_or_ref[1:]  # Remove $ prefix
            if ref_key in self._ref_key_index:
                full_identity = self._ref_key_index[ref_key]
                return self._registry[full_identity]

        raise ReferenceError(
            f"Reference '{identity_or_ref}' not found. Make sure it's defined before being referenced."
        )

    def has(self, identity: str) -> bool:
        """
        Check if identity is registered.

        Args:
            identity: Dotted path identity

        Returns:
            True if identity is registered
        """
        return identity in self._registry

    def all_identities(self) -> list[str]:
        """
        Get all registered identities in creation order.

        Returns:
            List of identity strings
        """
        return self._creation_order.copy()

    def count(self) -> int:
        """
        Get number of registered instances.

        Returns:
            Count of instances
        """
        return len(self._registry)

    def clear(self) -> None:
        """Clear all registered instances."""
        self._registry.clear()
        self._ref_key_index.clear()
        self._creation_order.clear()
        self._db_lookup_cache.clear()

    def get_from_db(self, model_class: type[models.Model], lookup_params: dict[str, Any]) -> models.Model:
        """
        Get an instance from the database using lookup parameters.

        Results are cached to avoid redundant queries.

        Args:
            model_class: Django model class to query
            lookup_params: Dictionary of field names to values for Django ORM lookup

        Returns:
            Django model instance

        Raises:
            ReferenceError: If object not found or multiple objects returned
        """
        # Create cache key
        cache_key = f"{model_class._meta.app_label}.{model_class.__name__}:{lookup_params}"

        # Check cache first
        if cache_key in self._db_lookup_cache:
            return self._db_lookup_cache[cache_key]

        # Query database
        try:
            instance = model_class.objects.get(**lookup_params)
            # Cache the result
            self._db_lookup_cache[cache_key] = instance
            return instance
        except ObjectDoesNotExist:
            lookup_str = ", ".join(f"{k}={v}" for k, v in lookup_params.items())
            raise ReferenceError(
                f"Database lookup failed: {model_class.__name__} with {lookup_str} does not exist. "
                f"Make sure the record exists in the database before referencing it."
            )
        except MultipleObjectsReturned:
            lookup_str = ", ".join(f"{k}={v}" for k, v in lookup_params.items())
            raise ReferenceError(
                f"Database lookup failed: Multiple {model_class.__name__} objects found with {lookup_str}. "
                f"Use more specific lookup parameters to uniquely identify the record."
            )
