"""Main loader orchestration with two-pass algorithm."""

from typing import Any, Callable

from django.db import transaction

from django_nested_seed.config.base import SeedConfig
from django_nested_seed.core.builder import DescriptorBuilder
from django_nested_seed.core.constants import (
    FIELD_SOURCE_IDENTITY,
    FIELD_SOURCE_FIELD,
    FIELD_TARGET_FIELD,
)
from django_nested_seed.core.parser import YAMLParser
from django_nested_seed.core.registry import ObjectDescriptor, ObjectRegistry
from django_nested_seed.core.resolver import ModelResolver
from django_nested_seed.relations.foreign_key import ForeignKeyHandler
from django_nested_seed.relations.one_to_one import OneToOneHandler
from django_nested_seed.relations.many_to_many import ManyToManyHandler
from django_nested_seed.utils.topological import topological_sort, flatten_descriptors


class SeedLoader:
    """
    Main orchestrator for two-pass loading algorithm.

    Responsibilities:
    - Coordinate all components
    - Execute two-pass algorithm:
      Pass 1: Create all objects with primitive fields and FK/O2O references
      Pass 2: Resolve and set M2M relationships
    - Handle topological sorting for dependencies
    - Provide verbose output
    """

    def __init__(self, config: SeedConfig, verbose: bool = False):
        """
        Initialize loader.

        Args:
            config: SeedConfig with mappings
            verbose: Enable verbose output
        """
        self.config = config
        self.verbose = verbose

        # Initialize components
        self.parser = YAMLParser()
        self.resolver = ModelResolver(config)
        self.builder = DescriptorBuilder(self.resolver, config)
        self.registry = ObjectRegistry()

        # Initialize relationship handlers
        self.fk_handler = ForeignKeyHandler()
        self.o2o_handler = OneToOneHandler()
        self.m2m_handler = ManyToManyHandler()

    def load(self, file_paths: list[str]) -> None:
        """
        Load seed data from YAML files.

        All operations wrapped in transaction - rolls back on any error.

        Args:
            file_paths: List of YAML file paths to load
        """
        with transaction.atomic():
            self._log(f"Loading seed data from {len(file_paths)} file(s): {', '.join(file_paths)}")

            # 1. Parse YAML files
            yaml_data = self.parser.parse_files(file_paths)

            self._execute_load(yaml_data)

    def load_from_string(self, yaml_content: str) -> None:
        """
        Load seed data from YAML string content.

        All operations wrapped in transaction - rolls back on any error.

        Args:
            yaml_content: YAML content as a string
        """
        with transaction.atomic():
            self._log("Loading seed data from string")

            # 1. Parse YAML string
            yaml_data = self.parser.parse_string(yaml_content)

            self._execute_load(yaml_data)

    def _execute_load(self, yaml_data: dict) -> None:
        """
        Execute the loading process for parsed YAML data.

        Args:
            yaml_data: Parsed YAML data
        """
        # 2. Build descriptors
        self._log("Building object descriptors...")
        top_level_descriptors = self.builder.build_descriptors(yaml_data)

        # Flatten to include nested children
        all_descriptors = flatten_descriptors(top_level_descriptors)
        self._log(
            f"Built {len(all_descriptors)} descriptors "
            f"({len(top_level_descriptors)} top-level, "
            f"{len(all_descriptors) - len(top_level_descriptors)} nested)"
        )

        # 3. Topological sort (only top-level descriptors)
        self._log("Sorting by dependencies...")
        sorted_top_level = topological_sort(top_level_descriptors, self.resolver)

        # 4. Pass 1: Create objects
        self._log("\nPass 1: Creating objects...")
        self._pass_one_create_objects(sorted_top_level)
        self._log(f"Pass 1 complete: {self.registry.count()} objects created")

        # 5. Pass 2: Resolve M2M
        m2m_count = sum(len(desc.m2m_fields) for desc in all_descriptors)
        through_count = sum(
            sum(len(children) for children in desc.m2m_inline_children.values())
            for desc in all_descriptors
        )
        if m2m_count > 0 or through_count > 0:
            self._log(f"\nPass 2: Resolving {m2m_count} M2M relationships and {through_count} through instances...")
            self._pass_two_resolve_m2m(all_descriptors)
            self._log(f"Pass 2 complete: {m2m_count} M2M relationships and {through_count} through instances resolved")

        self._log(
            f"\n✓ Successfully loaded {self.registry.count()} objects "
            f"with {m2m_count} M2M relationships"
        )

    def _pass_one_create_objects(self, descriptors: list[ObjectDescriptor]) -> None:
        """
        Pass 1: Create all objects with primitive fields and FK/O2O references.

        Args:
            descriptors: List of top-level ObjectDescriptors (already sorted)
        """
        for descriptor in descriptors:
            self._create_object_tree(descriptor)

    def _create_object_tree(self, descriptor: ObjectDescriptor) -> None:
        """
        Create an object and its nested children.

        Args:
            descriptor: ObjectDescriptor to create
        """
        # First, create any forward FK/O2O nested children (they need to exist before parent)
        forward_fk_children = []
        reverse_children = []

        for child_descriptor in descriptor.nested_children:
            # Check if this is a forward FK/O2O (has no parent_field_name)
            if child_descriptor.parent_field_name is None:
                forward_fk_children.append(child_descriptor)
            else:
                reverse_children.append(child_descriptor)

        # Create forward FK/O2O children first (before parent)
        # Need to recursively create their children too
        for child_descriptor in forward_fk_children:
            self._create_object_tree(child_descriptor)

        # Create the parent object (now that forward FKs exist)
        instance = self._create_object(descriptor)

        # Register it (with ref_key if explicitly defined)
        ref_key = descriptor.object_key if descriptor.has_explicit_ref else None
        self.registry.register(descriptor.identity, instance, ref_key=ref_key)
        self._log(f"  [{descriptor.identity}] Created {descriptor.model_class.__name__} ✓")

        # Create reverse nested children (OneToOne, reverse FK)
        for child_descriptor in reverse_children:
            self._create_nested_child(child_descriptor, instance)

        # Create inline M2M children (only non-through models in Pass 1)
        for field_name, inline_children in descriptor.m2m_inline_children.items():
            for child_descriptor in inline_children:
                # Skip through model instances - they'll be created in Pass 2
                if FIELD_SOURCE_IDENTITY not in child_descriptor.fields:
                    self._create_inline_m2m_child(child_descriptor)

    def _create_object(self, descriptor: ObjectDescriptor) -> Any:
        """
        Create a single object instance.

        Args:
            descriptor: ObjectDescriptor

        Returns:
            Created Django model instance
        """
        # Prepare field values
        prepared_fields = {}

        for field_name, value in descriptor.fields.items():
            prepared_value = self._resolve_field_value(
                field_name, value, descriptor.model_class
            )
            prepared_fields[field_name] = prepared_value

        # Create instance
        instance = descriptor.model_class(**prepared_fields)
        instance.save()

        return instance

    def _create_nested_child(
        self, child_descriptor: ObjectDescriptor, parent_instance: Any
    ) -> None:
        """
        Create a nested child object.

        Args:
            child_descriptor: ObjectDescriptor for child
            parent_instance: Parent model instance
        """
        # First, create any forward FK/O2O nested grandchildren (they need to exist before child)
        forward_fk_grandchildren = []
        reverse_grandchildren = []

        for grandchild_descriptor in child_descriptor.nested_children:
            # Check if this is a forward FK/O2O (has no parent_field_name)
            if grandchild_descriptor.parent_field_name is None:
                forward_fk_grandchildren.append(grandchild_descriptor)
            else:
                reverse_grandchildren.append(grandchild_descriptor)

        # Create forward FK/O2O grandchildren first
        for grandchild_descriptor in forward_fk_grandchildren:
            self._create_object_tree(grandchild_descriptor)

        # Set parent reference in fields
        if child_descriptor.parent_field_name:
            child_descriptor.fields[child_descriptor.parent_field_name] = parent_instance

        # Create the child
        child_instance = self._create_object(child_descriptor)

        # Register it (with ref_key if explicitly defined)
        ref_key = child_descriptor.object_key if child_descriptor.has_explicit_ref else None
        self.registry.register(child_descriptor.identity, child_instance, ref_key=ref_key)
        self._log(
            f"  [{child_descriptor.identity}] Created {child_descriptor.model_class.__name__} "
            f"(nested) ✓"
        )

        # Recursively create reverse nested grandchildren
        for grandchild_descriptor in reverse_grandchildren:
            self._create_nested_child(grandchild_descriptor, child_instance)

        # Create inline M2M children (only non-through models in Pass 1)
        for field_name, inline_children in child_descriptor.m2m_inline_children.items():
            for grandchild_descriptor in inline_children:
                # Skip through model instances - they'll be created in Pass 2
                if FIELD_SOURCE_IDENTITY not in grandchild_descriptor.fields:
                    self._create_inline_m2m_child(grandchild_descriptor)

    def _create_inline_m2m_child(self, child_descriptor: ObjectDescriptor) -> None:
        """
        Create an inline M2M child object or through model instance.

        Args:
            child_descriptor: Child ObjectDescriptor
        """
        # Check if this is a through model instance (has special source identity field)
        if FIELD_SOURCE_IDENTITY in child_descriptor.fields:
            self._create_through_instance(child_descriptor)
            return

        # Create forward FK/O2O children first
        forward_fk_children = []
        reverse_children = []

        for grandchild_descriptor in child_descriptor.nested_children:
            if grandchild_descriptor.parent_field_name is None:
                forward_fk_children.append(grandchild_descriptor)
            else:
                reverse_children.append(grandchild_descriptor)

        for grandchild_descriptor in forward_fk_children:
            self._create_object_tree(grandchild_descriptor)

        # Regular inline M2M child
        child_instance = self._create_object(child_descriptor)

        # Register it (with ref_key if explicitly defined)
        ref_key = child_descriptor.object_key if child_descriptor.has_explicit_ref else None
        self.registry.register(child_descriptor.identity, child_instance, ref_key=ref_key)
        self._log(
            f"  [{child_descriptor.identity}] Created {child_descriptor.model_class.__name__} "
            f"(inline M2M) ✓"
        )

        # Recursively create reverse nested children
        for grandchild_descriptor in reverse_children:
            self._create_nested_child(grandchild_descriptor, child_instance)

        # Recursively create its inline M2M children
        for field_name, inline_children in child_descriptor.m2m_inline_children.items():
            for grandchild_descriptor in inline_children:
                self._create_inline_m2m_child(grandchild_descriptor)

    def _create_through_instance(self, through_descriptor: ObjectDescriptor) -> None:
        """
        Create a through model instance for M2M with through.

        Args:
            through_descriptor: Descriptor for through model instance
        """
        # First, create any nested children (inline objects created within through model data)
        # These need to exist before we can reference them
        # Use _create_object_tree which handles nested children recursively
        for child_descriptor in through_descriptor.nested_children:
            self._create_object_tree(child_descriptor)

        # Extract special fields
        source_identity = through_descriptor.fields.pop(FIELD_SOURCE_IDENTITY)
        source_field_name = through_descriptor.fields.pop(FIELD_SOURCE_FIELD)
        target_field_name = through_descriptor.fields.pop(FIELD_TARGET_FIELD)

        # Resolve source and target instances
        source_instance = self.registry.get(source_identity)

        # Find target reference in fields
        target_reference = None
        target_field_obj = None
        for field_name, value in list(through_descriptor.fields.items()):
            if isinstance(value, str) and (self.resolver.is_reference_pattern(value) or self.resolver.is_db_lookup_pattern(value)):
                # Check if this field matches the target field
                if field_name == target_field_name:
                    target_reference = value
                    through_descriptor.fields.pop(field_name)
                    # Get field object for database lookups
                    try:
                        target_field_obj = through_descriptor.model_class._meta.get_field(target_field_name)
                    except Exception:
                        pass
                    break

        if not target_reference:
            # Try to find it in the first reference-like field
            for field_name, value in list(through_descriptor.fields.items()):
                if isinstance(value, str) and (self.resolver.is_reference_pattern(value) or self.resolver.is_db_lookup_pattern(value)):
                    target_reference = value
                    through_descriptor.fields.pop(field_name)
                    # Get field object for database lookups
                    try:
                        target_field_obj = through_descriptor.model_class._meta.get_field(field_name)
                    except Exception:
                        pass
                    break

        if not target_reference:
            raise ValueError(
                f"Could not find target reference in through model data for {through_descriptor.identity}"
            )

        # Resolve target instance (handles both $ref and @lookup)
        if self.resolver.is_db_lookup_pattern(target_reference):
            if target_field_obj and hasattr(target_field_obj, 'related_model'):
                target_model = target_field_obj.related_model
                lookup_params = self.resolver.parse_db_lookup(target_reference)
                target_instance = self.registry.get_from_db(target_model, lookup_params)
            else:
                raise ValueError(
                    f"Cannot resolve database lookup for through model: field not found or not a relation"
                )
        else:
            target_instance = self.registry.get(target_reference)

        # Add the FK references to fields
        through_descriptor.fields[source_field_name] = source_instance
        through_descriptor.fields[target_field_name] = target_instance

        # Create the through instance
        through_instance = self._create_object(through_descriptor)

        # Register it (with ref_key if explicitly defined)
        ref_key = through_descriptor.object_key if through_descriptor.has_explicit_ref else None
        self.registry.register(through_descriptor.identity, through_instance, ref_key=ref_key)
        self._log(
            f"  [{through_descriptor.identity}] Created {through_descriptor.model_class.__name__} "
            f"(through) ✓"
        )

    def _resolve_field_value(
        self, field_name: str, value: Any, model_class: type
    ) -> Any:
        """
        Resolve a field value, handling references and database lookups.

        Args:
            field_name: Field name
            value: Raw value
            model_class: Django model class

        Returns:
            Resolved value
        """
        # Check if it's a database lookup pattern
        if isinstance(value, str) and self.resolver.is_db_lookup_pattern(value):
            # Get the field
            try:
                field = model_class._meta.get_field(field_name)
            except Exception:
                # Field doesn't exist on model, return value as-is
                return value

            # Check if it's FK or O2O (database lookups only work for relationships)
            if self.fk_handler.can_handle(field) or self.o2o_handler.can_handle(field):
                # Get the related model
                related_model = field.related_model
                # Parse the lookup
                lookup_params = self.resolver.parse_db_lookup(value)
                # Fetch from database
                return self.registry.get_from_db(related_model, lookup_params)

        # Check if it's a reference pattern
        if isinstance(value, str) and self.resolver.is_reference_pattern(value):
            # Get the field
            try:
                field = model_class._meta.get_field(field_name)
            except Exception:
                # Field doesn't exist on model, return value as-is
                return value

            # Check if it's FK or O2O
            if self.fk_handler.can_handle(field):
                return self.fk_handler.prepare_value(value, self.registry)
            elif self.o2o_handler.can_handle(field):
                return self.o2o_handler.prepare_value(value, self.registry)

        # Return value as-is
        return value

    def _pass_two_resolve_m2m(self, descriptors: list[ObjectDescriptor]) -> None:
        """
        Pass 2: Resolve and set M2M relationships, including through models.

        Args:
            descriptors: All ObjectDescriptors (flattened, including nested)
        """
        for descriptor in descriptors:
            # Handle through model instances first
            if descriptor.m2m_inline_children:
                for field_name, inline_children in descriptor.m2m_inline_children.items():
                    for child_descriptor in inline_children:
                        # Create through model instances
                        if FIELD_SOURCE_IDENTITY in child_descriptor.fields:
                            self._create_through_instance(child_descriptor)

            # Handle standard M2M fields
            if not descriptor.m2m_fields:
                continue

            # Get the instance
            instance = self.registry.get(descriptor.identity)

            # Resolve each M2M field
            for field_name, references in descriptor.m2m_fields.items():
                self.m2m_handler.resolve_and_set(
                    instance, field_name, references, self.registry, self.resolver
                )
                self._log(
                    f"  [{descriptor.identity}] Set {field_name} ({len(references)} references) ✓"
                )

    def _log(self, message: str) -> None:
        """
        Log a message if verbose mode enabled.

        Args:
            message: Message to log
        """
        if self.verbose:
            print(message)
