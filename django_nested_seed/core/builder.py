"""Builds ObjectDescriptor trees from parsed YAML data."""

from typing import Any

from django_nested_seed.config.base import SeedConfig
from django_nested_seed.core.constants import (
    FIELD_SOURCE_IDENTITY,
    FIELD_SOURCE_FIELD,
    FIELD_TARGET_FIELD,
)
from django_nested_seed.core.registry import ObjectDescriptor
from django_nested_seed.core.resolver import ModelResolver
from django_nested_seed.core.exceptions import YAMLValidationError


class DescriptorBuilder:
    """
    Builds ObjectDescriptor trees from parsed YAML data.

    Responsibilities:
    - Traverse app_label -> collection -> object_key structure
    - Separate regular fields from nested objects and M2M fields
    - Build parent-child relationships for nested objects
    - Assign unique identities to all objects
    """

    def __init__(self, resolver: ModelResolver, config: SeedConfig):
        """
        Initialize builder.

        Args:
            resolver: ModelResolver for model lookup
            config: SeedConfig for nested relationship configuration
        """
        self.resolver = resolver
        self.config = config

    def build_descriptors(self, yaml_data: dict[str, Any]) -> list[ObjectDescriptor]:
        """
        Build list of ObjectDescriptors from parsed YAML data.

        Args:
            yaml_data: Parsed YAML with structure: app_label -> collection -> object_key -> fields

        Returns:
            List of top-level ObjectDescriptors (with nested_children populated)
        """
        all_descriptors = []

        for app_label, models_data in yaml_data.items():
            for model_name, objects in models_data.items():
                descriptors = self._process_model(app_label, model_name, objects)
                all_descriptors.extend(descriptors)

        return all_descriptors

    def _process_model(
        self, app_label: str, model_name: str, objects: list[dict[str, Any]]
    ) -> list[ObjectDescriptor]:
        """
        Process objects for a model.

        Args:
            app_label: Django app label
            model_name: Django model class name (e.g., "Category", "User")
            objects: List of object field dicts (may contain reference_key field)

        Returns:
            List of ObjectDescriptors for this model
        """
        model_class = self.resolver.resolve_model(app_label, model_name)
        descriptors = []
        reference_key = self.config.reference_key
        auto_key_counter = 0

        for fields_data in objects:
            # Extract reference key if present, otherwise auto-generate
            has_explicit_ref = False
            if reference_key in fields_data:
                object_key = fields_data[reference_key]
                has_explicit_ref = True
                # Remove reference key from fields
                fields_data = {k: v for k, v in fields_data.items() if k != reference_key}
            else:
                # Auto-generate key
                object_key = f"{model_name.lower()}_{auto_key_counter}"
                auto_key_counter += 1

            identity = f"{app_label}.{model_name}.{object_key}"

            descriptor = ObjectDescriptor(
                identity=identity,
                app_label=app_label,
                collection_name=model_name,  # Store model_name as collection_name for identity
                object_key=object_key,
                model_class=model_class,
                has_explicit_ref=has_explicit_ref,
            )

            self._process_object_fields(descriptor, fields_data)
            descriptors.append(descriptor)

        return descriptors

    def _process_object_fields(
        self, descriptor: ObjectDescriptor, fields_data: dict[str, Any]
    ) -> None:
        """
        Process fields for an object, separating primitives, references, M2M, and nested objects.

        Args:
            descriptor: ObjectDescriptor to populate
            fields_data: Dictionary of field name -> value
        """
        for field_name, value in fields_data.items():
            # Check if this is a nested dict - could be nested object
            if isinstance(value, dict):
                # Try to detect if this is a nested relationship using Django introspection
                nested_info = self.resolver.detect_nested_relationship(
                    descriptor.model_class, field_name
                )

                if nested_info:
                    # This is a nested relationship
                    self._process_nested_field(descriptor, field_name, value, nested_info)
                    continue

                # Check if it's configured explicitly
                nested_config = self.resolver.get_nested_config(
                    descriptor.model_class, field_name
                )
                if nested_config:
                    self._process_nested_field(descriptor, field_name, value, nested_config)
                    continue

                # Check if this is a forward ForeignKey or OneToOne field with nested object
                relationship_type = self.resolver.detect_relationship_type(
                    descriptor.model_class, field_name
                )
                if relationship_type in ("foreign_key", "one_to_one"):
                    # This is a nested forward FK/O2O - create inline object
                    self._process_nested_forward_fk(descriptor, field_name, value)
                    continue

                # Not a nested relationship, might be a JSON field or error
                # For now, treat as regular field
                descriptor.fields[field_name] = value
                continue

            # Check if this is a list (could be nested FK collection or M2M)
            if isinstance(value, list):
                # First check if it's a nested relationship
                nested_info = self.resolver.detect_nested_relationship(
                    descriptor.model_class, field_name
                )

                if nested_info and nested_info.relation_type == "foreign_key":
                    # This is a nested FK collection in list format
                    self._process_nested_list_field(descriptor, field_name, value, nested_info)
                    continue

                # Check if any item is a reference (YAML ref or database lookup) or dict
                has_references = any(self.resolver.is_any_reference(v) for v in value if isinstance(v, str))
                has_dicts = any(isinstance(v, dict) for v in value)

                if has_references or has_dicts:
                    # This is an M2M field with references and/or inline definitions
                    self._process_m2m_field(descriptor, field_name, value)
                    continue

            # Regular field (primitive, FK/O2O reference, or other)
            descriptor.fields[field_name] = value

    def _process_nested_field(
        self,
        parent_descriptor: ObjectDescriptor,
        nested_key: str,
        nested_data: dict[str, Any],
        nested_config: Any,
    ) -> None:
        """
        Process a nested field (OneToOne or nested ForeignKey collection).

        Args:
            parent_descriptor: Parent ObjectDescriptor
            nested_key: Nested key in YAML
            nested_data: Nested data (dict for O2O, dict of objects for FK)
            nested_config: NestedRelationConfig
        """
        if nested_config.relation_type == "one_to_one":
            # OneToOne: nested_data is a single object's fields
            child_descriptor = self._create_nested_one_to_one(
                parent_descriptor, nested_key, nested_data, nested_config
            )
            parent_descriptor.nested_children.append(child_descriptor)

        elif nested_config.relation_type == "foreign_key":
            # ForeignKey collection: nested_data is dict of object_key -> fields
            child_descriptors = self._create_nested_foreign_key_collection(
                parent_descriptor, nested_key, nested_data, nested_config
            )
            parent_descriptor.nested_children.extend(child_descriptors)

    def _create_nested_one_to_one(
        self,
        parent_descriptor: ObjectDescriptor,
        nested_key: str,
        fields_data: dict[str, Any],
        nested_config: Any,
    ) -> ObjectDescriptor:
        """
        Create descriptor for nested OneToOne object.

        For OneToOne, we don't give it a separate identity - it's part of the parent.

        Args:
            parent_descriptor: Parent ObjectDescriptor
            nested_key: Nested key in YAML
            fields_data: Field values for nested object
            nested_config: NestedRelationConfig

        Returns:
            ObjectDescriptor for nested object
        """
        # Parse target model
        target_app_label, target_model_name = nested_config.target_model.split(".")
        target_model_class = self.resolver.resolve_model(target_app_label, target_model_name)

        # For O2O, identity is parent_identity.nested_key (not separately referenceable)
        identity = f"{parent_descriptor.identity}.{nested_key}"

        child_descriptor = ObjectDescriptor(
            identity=identity,
            app_label=target_app_label,
            collection_name=target_model_name,  # Use actual model name
            object_key=nested_key,
            model_class=target_model_class,
            parent_descriptor=parent_descriptor,
            parent_field_name=nested_config.reverse_field_name,
        )

        self._process_object_fields(child_descriptor, fields_data)
        return child_descriptor

    def _create_nested_foreign_key_collection(
        self,
        parent_descriptor: ObjectDescriptor,
        nested_key: str,
        objects_data: dict[str, Any],
        nested_config: Any,
    ) -> list[ObjectDescriptor]:
        """
        Create descriptors for nested ForeignKey collection.

        For nested FK, each child gets a full identity: app_label.collection.object_key

        Args:
            parent_descriptor: Parent ObjectDescriptor
            nested_key: Nested key in YAML
            objects_data: Dictionary of object_key -> fields
            nested_config: NestedRelationConfig

        Returns:
            List of ObjectDescriptors for nested objects
        """
        # Parse target model
        target_app_label, target_model_name = nested_config.target_model.split(".")

        # Resolve the target model directly by model name
        target_model_class = self.resolver.resolve_model(target_app_label, target_model_name)

        child_descriptors = []

        for object_key, fields_data in objects_data.items():
            # Full identity for nested FK children (can be referenced from M2M fields)
            identity = f"{target_app_label}.{target_model_name}.{object_key}"

            child_descriptor = ObjectDescriptor(
                identity=identity,
                app_label=target_app_label,
                collection_name=target_model_name,  # Use actual model name
                object_key=object_key,
                model_class=target_model_class,
                parent_descriptor=parent_descriptor,
                parent_field_name=nested_config.reverse_field_name,
            )

            self._process_object_fields(child_descriptor, fields_data)
            child_descriptors.append(child_descriptor)

        return child_descriptors

    def _process_nested_list_field(
        self,
        parent_descriptor: ObjectDescriptor,
        nested_key: str,
        objects_list: list[dict[str, Any]],
        nested_config: Any,
    ) -> None:
        """
        Process a nested FK collection in list format.

        Args:
            parent_descriptor: Parent ObjectDescriptor
            nested_key: Nested key in YAML
            objects_list: List of object dicts (may contain $ref)
            nested_config: NestedRelationConfig
        """
        # Parse target model
        target_app_label, target_model_name = nested_config.target_model.split(".")
        target_model_class = self.resolver.resolve_model(target_app_label, target_model_name)

        child_descriptors = []
        reference_key = self.config.reference_key
        auto_key_counter = 0

        for fields_data in objects_list:
            # Extract reference key if present, otherwise auto-generate
            has_explicit_ref = False
            if reference_key in fields_data:
                object_key = fields_data[reference_key]
                has_explicit_ref = True
                # Remove reference key from fields
                fields_data = {k: v for k, v in fields_data.items() if k != reference_key}
            else:
                # Auto-generate key with parent context to avoid conflicts in nested hierarchies
                object_key = f"{parent_descriptor.object_key}_{nested_key}_{auto_key_counter}"
                auto_key_counter += 1

            # Full identity for nested FK children (can be referenced from M2M fields)
            identity = f"{target_app_label}.{target_model_name}.{object_key}"

            child_descriptor = ObjectDescriptor(
                identity=identity,
                app_label=target_app_label,
                collection_name=target_model_name,
                object_key=object_key,
                model_class=target_model_class,
                parent_descriptor=parent_descriptor,
                parent_field_name=nested_config.reverse_field_name,
                has_explicit_ref=has_explicit_ref,
            )

            self._process_object_fields(child_descriptor, fields_data)
            child_descriptors.append(child_descriptor)

        parent_descriptor.nested_children.extend(child_descriptors)

    def _process_nested_forward_fk(
        self,
        parent_descriptor: ObjectDescriptor,
        field_name: str,
        nested_data: dict[str, Any],
    ) -> None:
        """
        Process a nested forward ForeignKey or OneToOne field.

        Args:
            parent_descriptor: Parent ObjectDescriptor
            field_name: FK/O2O field name
            nested_data: Nested object data (dict)
        """
        # Get the field to determine target model
        try:
            field = parent_descriptor.model_class._meta.get_field(field_name)
            target_model = field.related_model
            target_app_label = target_model._meta.app_label
            target_model_name = target_model.__name__
        except Exception:
            # Field doesn't exist, treat as regular field
            parent_descriptor.fields[field_name] = nested_data
            return

        # Extract reference key if present, otherwise auto-generate
        reference_key = self.config.reference_key
        has_explicit_ref = False
        if reference_key in nested_data:
            object_key = nested_data[reference_key]
            has_explicit_ref = True
            # Remove reference key from fields
            nested_data = {k: v for k, v in nested_data.items() if k != reference_key}
        else:
            # Auto-generate key for inline FK object
            object_key = f"{parent_descriptor.object_key}_{field_name}"

        # Create identity for the nested FK object
        identity = f"{target_app_label}.{target_model_name}.{object_key}"

        # Create descriptor for the nested FK object
        nested_descriptor = ObjectDescriptor(
            identity=identity,
            app_label=target_app_label,
            collection_name=target_model_name,
            object_key=object_key,
            model_class=target_model,
            has_explicit_ref=has_explicit_ref,
        )

        # Process the nested object's fields
        self._process_object_fields(nested_descriptor, nested_data)

        # Store the nested object's identity as a reference in the parent's field
        parent_descriptor.fields[field_name] = identity

        # Add to parent's nested children so it gets created first
        parent_descriptor.nested_children.insert(0, nested_descriptor)

    def _process_m2m_field(
        self,
        descriptor: ObjectDescriptor,
        field_name: str,
        value: list[Any],
    ) -> None:
        """
        Process a M2M field that may contain references and/or inline object definitions.
        Also handles M2M with through models.

        Args:
            descriptor: ObjectDescriptor to populate
            field_name: M2M field name
            value: List containing reference strings and/or dicts
        """
        references = []
        inline_children = []

        # Get the M2M field to determine target model
        try:
            m2m_field = descriptor.model_class._meta.get_field(field_name)
            target_model = m2m_field.related_model
            target_app_label = target_model._meta.app_label
            target_model_name = target_model.__name__

            # Check if this M2M has a custom through model
            through_model = m2m_field.remote_field.through
            has_custom_through = not through_model._meta.auto_created
        except Exception:
            # If we can't introspect, treat as regular field
            descriptor.fields[field_name] = value
            return

        # If has custom through model, handle differently
        if has_custom_through:
            self._process_m2m_through_field(
                descriptor, field_name, value, through_model, m2m_field
            )
            return

        # Standard M2M without through model
        for item in value:
            if isinstance(item, str) and self.resolver.is_any_reference(item):
                # Reference string (can be $ref or @lookup)
                references.append(item)
            elif isinstance(item, dict):
                # Inline object definition
                # Generate a unique key for this inline object
                inline_key = f"{descriptor.object_key}_{field_name}_{len(inline_children)}"
                identity = f"{target_app_label}.{target_model_name}.{inline_key}"

                child_descriptor = ObjectDescriptor(
                    identity=identity,
                    app_label=target_app_label,
                    collection_name=target_model_name,
                    object_key=inline_key,
                    model_class=target_model,
                )

                self._process_object_fields(child_descriptor, item)
                inline_children.append(child_descriptor)
                # Add the identity to references so it can be resolved later
                references.append(identity)

        # Store both references and inline children
        if references:
            descriptor.m2m_fields[field_name] = references
        if inline_children:
            descriptor.m2m_inline_children[field_name] = inline_children

    def _process_m2m_through_field(
        self,
        descriptor: ObjectDescriptor,
        field_name: str,
        value: list[Any],
        through_model: type,
        m2m_field: Any,
    ) -> None:
        """
        Process a M2M field with a custom through model.

        Args:
            descriptor: ObjectDescriptor to populate
            field_name: M2M field name
            value: List of dicts with through model data
            through_model: The through model class
            m2m_field: The M2M field object
        """
        through_children = []
        through_app_label = through_model._meta.app_label
        through_model_name = through_model.__name__

        # Determine the field names on the through model
        # Usually: source_field (e.g., 'team') and target_field (e.g., 'user')
        # Find which field points to our model (descriptor.model_class)
        source_field_name = None
        target_field_name = None

        for field in through_model._meta.get_fields():
            if hasattr(field, 'related_model'):
                if field.related_model == descriptor.model_class:
                    source_field_name = field.name
                elif field.related_model == m2m_field.related_model:
                    target_field_name = field.name

        for idx, item in enumerate(value):
            if not isinstance(item, dict):
                # Skip non-dict items (could be references in mixed usage)
                continue

            # Generate identity for through model instance
            through_key = f"{descriptor.object_key}_{field_name}_{idx}"
            through_identity = f"{through_app_label}.{through_model_name}.{through_key}"

            # Create descriptor for through model instance
            through_descriptor = ObjectDescriptor(
                identity=through_identity,
                app_label=through_app_label,
                collection_name=through_model_name,
                object_key=through_key,
                model_class=through_model,
            )

            # Copy fields from item to through_descriptor
            # The item should contain the target reference and extra fields
            through_fields = dict(item)

            # Add the source field reference (points back to parent)
            # This will be resolved when creating the through instance
            through_descriptor.fields[FIELD_SOURCE_IDENTITY] = descriptor.identity
            through_descriptor.fields[FIELD_SOURCE_FIELD] = source_field_name
            through_descriptor.fields[FIELD_TARGET_FIELD] = target_field_name

            # Process inline object creation for FK fields on the through model
            # This allows users to inline create related objects (e.g., User) within the through data
            for field_name, field_value in list(through_fields.items()):
                if isinstance(field_value, dict):
                    # Check if this field is a FK on the through model
                    try:
                        field = through_model._meta.get_field(field_name)
                        if hasattr(field, 'related_model') and field.related_model:
                            # This is a FK field with inline object definition
                            inline_model = field.related_model
                            inline_app_label = inline_model._meta.app_label
                            inline_model_name = inline_model.__name__

                            # Extract or generate object key
                            reference_key = self.config.reference_key
                            has_explicit_ref = False
                            if reference_key in field_value:
                                inline_object_key = field_value[reference_key]
                                has_explicit_ref = True
                                field_value = {k: v for k, v in field_value.items() if k != reference_key}
                            else:
                                # Auto-generate key for inline object
                                inline_object_key = f"{through_key}_{field_name}"

                            # Create identity for the inline object
                            inline_identity = f"{inline_app_label}.{inline_model_name}.{inline_object_key}"

                            # Create descriptor for the inline object
                            inline_descriptor = ObjectDescriptor(
                                identity=inline_identity,
                                app_label=inline_app_label,
                                collection_name=inline_model_name,
                                object_key=inline_object_key,
                                model_class=inline_model,
                                has_explicit_ref=has_explicit_ref,
                            )

                            # Process the inline object's fields
                            self._process_object_fields(inline_descriptor, field_value)

                            # Replace the dict with the identity reference
                            through_fields[field_name] = inline_identity

                            # Add to through descriptor's nested children so it gets created first
                            through_descriptor.nested_children.insert(0, inline_descriptor)
                    except Exception:
                        # Field doesn't exist or isn't a FK, leave as-is
                        pass

            # Process the fields (including the target reference)
            self._process_object_fields(through_descriptor, through_fields)

            through_children.append(through_descriptor)

        # Store through children
        if through_children:
            descriptor.m2m_inline_children[field_name] = through_children
