"""YAML parsing and validation for nested seed data."""

import yaml
from pathlib import Path
from typing import Any

from django_nested_seed.core.exceptions import YAMLValidationError


class YAMLParser:
    """
    Parser for nested YAML seed data files.

    Handles:
    - Loading YAML files with UTF-8 encoding
    - Merging multiple YAML files (later files override earlier)
    - Validating structure: app_label -> collection -> object_key -> fields
    """

    def parse_files(self, file_paths: list[str]) -> dict[str, Any]:
        """
        Parse and merge multiple YAML files.

        Args:
            file_paths: List of YAML file paths to load

        Returns:
            Merged dictionary with structure: app_label -> collection -> object_key -> fields

        Raises:
            YAMLValidationError: If files cannot be loaded or structure is invalid
        """
        yaml_dicts = []

        for file_path in file_paths:
            yaml_data = self._load_yaml(file_path)
            yaml_dicts.append(yaml_data)

        merged_data = self._merge_yaml_data(yaml_dicts)
        self._validate_structure(merged_data)

        return merged_data

    def parse_string(self, yaml_content: str) -> dict[str, Any]:
        """
        Parse YAML content from a string.

        Args:
            yaml_content: YAML content as a string

        Returns:
            Parsed dictionary with structure: app_label -> collection -> object_key -> fields

        Raises:
            YAMLValidationError: If content cannot be parsed or structure is invalid
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise YAMLValidationError(f"Failed to parse YAML content: {e}")

        if data is None:
            # Empty content
            return {}

        if not isinstance(data, dict):
            raise YAMLValidationError(
                f"YAML content must contain a dictionary at root level, got {type(data).__name__}"
            )

        self._validate_structure(data)
        return data

    def _load_yaml(self, file_path: str) -> dict[str, Any]:
        """
        Load a single YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML as dictionary

        Raises:
            YAMLValidationError: If file cannot be loaded or parsed
        """
        path = Path(file_path)

        if not path.exists():
            raise YAMLValidationError(f"YAML file not found: {file_path}")

        if not path.is_file():
            raise YAMLValidationError(f"Path is not a file: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise YAMLValidationError(f"Failed to parse YAML file {file_path}: {e}")
        except Exception as e:
            raise YAMLValidationError(f"Failed to read file {file_path}: {e}")

        if data is None:
            # Empty file
            return {}

        if not isinstance(data, dict):
            raise YAMLValidationError(
                f"YAML file {file_path} must contain a dictionary at root level, got {type(data).__name__}"
            )

        return data

    def _merge_yaml_data(self, yaml_dicts: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Merge multiple YAML dictionaries.

        Later dictionaries override earlier ones at all levels.

        Args:
            yaml_dicts: List of dictionaries to merge

        Returns:
            Merged dictionary
        """
        if not yaml_dicts:
            return {}

        merged = {}

        for yaml_dict in yaml_dicts:
            merged = self._deep_merge(merged, yaml_dict)

        return merged

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Dictionary to merge on top of base

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override value
                result[key] = value

        return result

    def _validate_structure(self, data: dict[str, Any]) -> None:
        """
        Validate YAML structure matches specification.

        Expected structure:
        app_label (str) -> collection (str) -> objects (list)

        List format: [fields (dict), fields (dict), ...]
        Objects may contain a special reference key field (e.g., $ref) for explicit identities.

        Args:
            data: Parsed YAML data

        Raises:
            YAMLValidationError: If structure is invalid
        """
        if not data:
            # Empty data is valid (no-op)
            return

        for app_label, collections in data.items():
            if not isinstance(app_label, str):
                raise YAMLValidationError(
                    f"App label must be a string, got {type(app_label).__name__}: {app_label}"
                )

            if not isinstance(collections, dict):
                raise YAMLValidationError(
                    f"App '{app_label}' must contain a dictionary of collections, "
                    f"got {type(collections).__name__}"
                )

            for collection_name, objects in collections.items():
                if not isinstance(collection_name, str):
                    raise YAMLValidationError(
                        f"Collection name in app '{app_label}' must be a string, "
                        f"got {type(collection_name).__name__}: {collection_name}"
                    )

                # Objects must be a list
                if not isinstance(objects, list):
                    raise YAMLValidationError(
                        f"Collection '{app_label}.{collection_name}' must contain a list of objects, "
                        f"got {type(objects).__name__}. Each object should be a dictionary."
                    )

                # Validate each item is a dict
                for idx, fields in enumerate(objects):
                    if not isinstance(fields, dict):
                        raise YAMLValidationError(
                            f"List item {idx} in '{app_label}.{collection_name}' must be a dictionary of fields, "
                            f"got {type(fields).__name__}"
                        )
