"""Configuration system for model mappings and nested relationships."""

from dataclasses import dataclass, field
from typing import Any

from django.conf import settings


@dataclass
class NestedRelationConfig:
    """
    Configuration for a nested relationship.

    Attributes:
        nested_key: Key in YAML that represents this nested relationship (e.g., "profile", "teams")
        target_model: Full model path (e.g., "accounts.Profile", "org.Team")
        relation_type: Type of relationship ("one_to_one" or "foreign_key")
        reverse_field_name: Field name on the child model that points to parent
    """

    nested_key: str
    target_model: str  # "app_label.ModelName"
    relation_type: str  # "one_to_one" or "foreign_key"
    reverse_field_name: str

    def __post_init__(self):
        if self.relation_type not in ("one_to_one", "foreign_key"):
            raise ValueError(
                f"relation_type must be 'one_to_one' or 'foreign_key', got '{self.relation_type}'"
            )


@dataclass
class ModelMapping:
    """
    Maps a collection to a Django model.

    Attributes:
        app_label: Django app label (e.g., "accounts", "org")
        collection_name: Collection name in YAML (e.g., "users", "companies")
        model_path: Full model path (e.g., "accounts.User", "org.Company")
        nested_relations: List of nested relationship configurations
    """

    app_label: str
    collection_name: str
    model_path: str  # "app_label.ModelName"
    nested_relations: list[NestedRelationConfig] = field(default_factory=list)


class SeedConfig:
    """
    Main configuration object for nested seed.

    Manages collection-to-model mappings and nested relationship configurations.
    Supports both explicit mappings and auto-discovery fallback.
    """

    def __init__(
        self,
        mappings: list[ModelMapping] | None = None,
        reference_key: str = "$ref"
    ):
        """
        Initialize configuration with optional explicit mappings.

        Args:
            mappings: List of explicit model mappings
            reference_key: Field name used for explicit object references (default: "$ref")
        """
        self._mappings: dict[tuple[str, str], ModelMapping] = {}
        self._nested_configs: dict[tuple[str, str], list[NestedRelationConfig]] = {}
        self.reference_key = reference_key

        if mappings:
            for mapping in mappings:
                self.add_mapping(mapping)

    def add_mapping(self, mapping: ModelMapping) -> None:
        """
        Add a model mapping to the configuration.

        Args:
            mapping: ModelMapping to add
        """
        key = (mapping.app_label, mapping.collection_name)
        self._mappings[key] = mapping

        # Index nested relations by model path
        if mapping.nested_relations:
            nested_key = (mapping.app_label, mapping.model_path.split(".")[-1])
            if nested_key not in self._nested_configs:
                self._nested_configs[nested_key] = []
            self._nested_configs[nested_key].extend(mapping.nested_relations)

    def get_model_path(self, app_label: str, collection_name: str) -> str | None:
        """
        Get the model path for a collection.

        Returns None if no explicit mapping exists (caller should try auto-discovery).

        Args:
            app_label: Django app label
            collection_name: Collection name

        Returns:
            Model path (e.g., "accounts.User") or None if not found
        """
        key = (app_label, collection_name)
        mapping = self._mappings.get(key)
        return mapping.model_path if mapping else None

    def get_nested_config(
        self, app_label: str, model_name: str, nested_key: str
    ) -> NestedRelationConfig | None:
        """
        Get nested relationship configuration for a model and nested key.

        Args:
            app_label: Django app label
            model_name: Model name (not full path, just the class name)
            nested_key: Nested key in YAML (e.g., "profile", "teams")

        Returns:
            NestedRelationConfig if found, None otherwise
        """
        lookup_key = (app_label, model_name)
        configs = self._nested_configs.get(lookup_key, [])

        for config in configs:
            if config.nested_key == nested_key:
                return config

        return None

    def get_all_nested_configs(
        self, app_label: str, model_name: str
    ) -> list[NestedRelationConfig]:
        """
        Get all nested relationship configurations for a model.

        Args:
            app_label: Django app label
            model_name: Model name (not full path, just the class name)

        Returns:
            List of NestedRelationConfig objects (empty if none found)
        """
        lookup_key = (app_label, model_name)
        return self._nested_configs.get(lookup_key, [])

    @classmethod
    def from_django_settings(cls) -> "SeedConfig":
        """
        Create configuration from Django settings.

        Looks for NESTED_SEED_CONFIG in settings with structure:
        {
            'reference_key': '$ref',  # Optional, defaults to '$ref'
            'mappings': [
                {
                    'app_label': 'accounts',
                    'collection_name': 'users',
                    'model_path': 'accounts.User',
                    'nested_relations': [
                        {
                            'nested_key': 'profile',
                            'target_model': 'accounts.Profile',
                            'relation_type': 'one_to_one',
                            'reverse_field_name': 'user',
                        }
                    ]
                },
            ]
        }

        Returns:
            SeedConfig instance with mappings from settings
        """
        config_dict = getattr(settings, "NESTED_SEED_CONFIG", {})
        mappings_data = config_dict.get("mappings", [])
        reference_key = config_dict.get("reference_key", "$ref")

        mappings = []
        for mapping_data in mappings_data:
            nested_relations_data = mapping_data.get("nested_relations", [])
            nested_relations = [
                NestedRelationConfig(
                    nested_key=nr["nested_key"],
                    target_model=nr["target_model"],
                    relation_type=nr["relation_type"],
                    reverse_field_name=nr["reverse_field_name"],
                )
                for nr in nested_relations_data
            ]

            mapping = ModelMapping(
                app_label=mapping_data["app_label"],
                collection_name=mapping_data["collection_name"],
                model_path=mapping_data["model_path"],
                nested_relations=nested_relations,
            )
            mappings.append(mapping)

        return cls(mappings=mappings, reference_key=reference_key)
