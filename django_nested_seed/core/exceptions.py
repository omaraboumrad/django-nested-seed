"""Custom exceptions for django-nested-seed."""


class NestedSeedError(Exception):
    """Base exception for all nested seed errors."""

    pass


class YAMLValidationError(NestedSeedError):
    """Raised when YAML structure is invalid."""

    pass


class ModelResolutionError(NestedSeedError):
    """Raised when a model cannot be resolved from collection name."""

    pass


class ReferenceError(NestedSeedError):
    """Raised when a reference cannot be resolved."""

    pass


class CircularDependencyError(NestedSeedError):
    """Raised when circular dependencies are detected."""

    pass
