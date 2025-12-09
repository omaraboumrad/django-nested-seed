"""Model resolution with hybrid auto-discovery and explicit configuration."""

import re
from typing import Any

from django.apps import apps
from django.db import models
from django.db.models import (
    ForeignKey,
    OneToOneField,
    ManyToManyField,
    Field,
)

from django_nested_seed.config.base import SeedConfig, NestedRelationConfig
from django_nested_seed.core.exceptions import ModelResolutionError


class ModelResolver:
    """
    Resolves model names to Django models.

    Uses direct model name resolution:
    1. Check explicit configuration first (for rare override cases)
    2. Use model name directly with Django's app registry
    3. Provides field introspection for relationship detection
    """

    # Pattern for reference strings: $ref_key or app_label.ModelName.object_key (legacy)
    # $ref_key format: $followed_by_ref_name
    # Legacy format: app_label.ModelName.object_key
    REFERENCE_PATTERN = re.compile(r"^\$[a-z_][a-z0-9_]*$|^[a-z_][a-z0-9_]*\.[A-Z][A-Za-z0-9_]*\.[a-z_][a-z0-9_]*$")

    def __init__(self, config: SeedConfig):
        """
        Initialize resolver with configuration.

        Args:
            config: SeedConfig with explicit mappings
        """
        self.config = config

    def resolve_model(self, app_label: str, model_name: str) -> type[models.Model]:
        """
        Resolve model name to Django model class.

        The model_name is used directly as the Django model class name.
        No pluralization or transformation - what you write is what you get.

        Args:
            app_label: Django app label
            model_name: Exact Django model class name (e.g., "Category", "User")

        Returns:
            Django model class

        Raises:
            ModelResolutionError: If model cannot be resolved
        """
        # Try explicit config first (for rare cases where you need override)
        model_class = self._resolve_from_config(app_label, model_name)
        if model_class:
            return model_class

        # Use model_name directly - no transformation
        try:
            return apps.get_model(app_label, model_name)
        except LookupError as e:
            raise ModelResolutionError(
                f"Model '{app_label}.{model_name}' not found. "
                f"Make sure the model exists and the app is in INSTALLED_APPS. "
                f"Error: {e}"
            )

    def _resolve_from_config(
        self, app_label: str, collection_name: str
    ) -> type[models.Model] | None:
        """
        Try to resolve model from explicit configuration.

        Args:
            app_label: Django app label
            collection_name: Collection name

        Returns:
            Model class if found in config, None otherwise
        """
        model_path = self.config.get_model_path(app_label, collection_name)
        if not model_path:
            return None

        # Parse model path: "app_label.ModelName"
        parts = model_path.split(".")
        if len(parts) != 2:
            raise ModelResolutionError(
                f"Invalid model path in config: '{model_path}'. Expected format: 'app_label.ModelName'"
            )

        config_app_label, model_name = parts

        try:
            return apps.get_model(config_app_label, model_name)
        except LookupError as e:
            raise ModelResolutionError(
                f"Model '{model_path}' from config not found in Django apps: {e}"
            )

    def is_reference_pattern(self, value: Any) -> bool:
        """
        Check if a value matches the reference pattern.

        Reference pattern: app_label.ModelName.object_key
        Example: auth.User.admin, testapp.Category.django

        Args:
            value: Value to check

        Returns:
            True if value is a string matching reference pattern
        """
        if not isinstance(value, str):
            return False

        return bool(self.REFERENCE_PATTERN.match(value))

    def get_model_fields(self, model_class: type[models.Model]) -> dict[str, Field]:
        """
        Get all fields for a Django model.

        Args:
            model_class: Django model class

        Returns:
            Dictionary mapping field name to Field instance
        """
        fields = {}
        for field in model_class._meta.get_fields():
            if hasattr(field, "name"):
                fields[field.name] = field
        return fields

    def detect_relationship_type(
        self, model_class: type[models.Model], field_name: str
    ) -> str | None:
        """
        Detect the type of relationship for a field.

        Args:
            model_class: Django model class
            field_name: Field name to check

        Returns:
            "foreign_key", "one_to_one", "many_to_many", or None if not a relationship
        """
        try:
            field = model_class._meta.get_field(field_name)
        except Exception:
            return None

        if isinstance(field, ForeignKey):
            return "foreign_key"
        elif isinstance(field, OneToOneField):
            return "one_to_one"
        elif isinstance(field, ManyToManyField):
            return "many_to_many"

        return None

    def get_nested_config(
        self, model_class: type[models.Model], nested_key: str
    ) -> NestedRelationConfig | None:
        """
        Get nested relationship configuration for a model.

        Args:
            model_class: Django model class
            nested_key: Nested key from YAML

        Returns:
            NestedRelationConfig if found, None otherwise
        """
        app_label = model_class._meta.app_label
        model_name = model_class.__name__

        return self.config.get_nested_config(app_label, model_name, nested_key)

    def get_all_nested_configs(
        self, model_class: type[models.Model]
    ) -> list[NestedRelationConfig]:
        """
        Get all nested relationship configurations for a model.

        Args:
            model_class: Django model class

        Returns:
            List of NestedRelationConfig objects
        """
        app_label = model_class._meta.app_label
        model_name = model_class.__name__

        return self.config.get_all_nested_configs(app_label, model_name)

    def is_field_on_model(self, model_class: type[models.Model], field_name: str) -> bool:
        """
        Check if a field exists on a model.

        Args:
            model_class: Django model class
            field_name: Field name to check

        Returns:
            True if field exists on model
        """
        try:
            model_class._meta.get_field(field_name)
            return True
        except Exception:
            return False

    def detect_nested_relationship(
        self, model_class: type[models.Model], nested_key: str
    ) -> NestedRelationConfig | None:
        """
        Auto-detect nested relationships using Django's reverse relationship introspection.

        Checks if nested_key matches:
        1. A OneToOneField accessor (reverse of OneToOne pointing to this model)
        2. A related_name from a ForeignKey pointing to this model
        3. A default reverse accessor ({model}_set) from a ForeignKey

        Args:
            model_class: Parent model class
            nested_key: Key in YAML that might be a nested relationship

        Returns:
            NestedRelationConfig if detected, None otherwise
        """
        # Get all related objects (reverse relationships)
        related_objects = [
            f for f in model_class._meta.get_fields()
            if (f.one_to_many or f.one_to_one) and f.auto_created
        ]

        for related in related_objects:
            # Get the accessor name (related_name or default)
            accessor_name = related.get_accessor_name()

            if accessor_name == nested_key:
                # Found a matching reverse relationship!
                related_model = related.related_model
                reverse_field_name = related.field.name

                # Determine if it's OneToOne or ForeignKey
                if related.one_to_one:
                    relation_type = "one_to_one"
                else:
                    relation_type = "foreign_key"

                # Build the target model path
                target_model = f"{related_model._meta.app_label}.{related_model.__name__}"

                return NestedRelationConfig(
                    nested_key=nested_key,
                    target_model=target_model,
                    relation_type=relation_type,
                    reverse_field_name=reverse_field_name,
                )

        return None
