"""Topological sorting for dependency resolution."""

from django_nested_seed.core.registry import ObjectDescriptor
from django_nested_seed.core.resolver import ModelResolver
from django_nested_seed.core.exceptions import CircularDependencyError


def topological_sort(
    descriptors: list[ObjectDescriptor], resolver: ModelResolver
) -> list[ObjectDescriptor]:
    """
    Sort descriptors by FK dependencies using DFS.

    Returns list in creation order (dependencies first).

    Args:
        descriptors: List of ObjectDescriptors to sort
        resolver: ModelResolver for checking reference patterns

    Returns:
        List of ObjectDescriptors in topological order

    Raises:
        CircularDependencyError: If circular dependencies detected
    """
    # Build identity -> descriptor mapping
    descriptor_map = {desc.identity: desc for desc in descriptors}

    # Build dependency graph: identity -> list of identities it depends on
    dependencies = {}
    for desc in descriptors:
        deps = []
        for field_name, value in desc.fields.items():
            if isinstance(value, str) and resolver.is_reference_pattern(value):
                # This is a FK/O2O reference
                deps.append(value)
        dependencies[desc.identity] = deps

    # Topological sort using DFS
    visited = set()
    visiting = set()  # For cycle detection
    result = []

    def visit(identity: str, path: list[str]):
        """
        DFS visit function.

        Args:
            identity: Current node identity
            path: Path taken to reach this node (for cycle detection)
        """
        if identity in visited:
            return

        if identity in visiting:
            # Cycle detected
            cycle_path = " -> ".join(path + [identity])
            raise CircularDependencyError(
                f"Circular dependency detected: {cycle_path}"
            )

        visiting.add(identity)

        # Visit dependencies first
        for dep_identity in dependencies.get(identity, []):
            if dep_identity in descriptor_map:
                # Only follow dependencies that are in our descriptor list
                visit(dep_identity, path + [identity])

        visiting.remove(identity)
        visited.add(identity)

        # Add to result after all dependencies processed
        if identity in descriptor_map:
            result.append(descriptor_map[identity])

    # Visit all descriptors
    for desc in descriptors:
        if desc.identity not in visited:
            visit(desc.identity, [])

    return result


def flatten_descriptors(descriptors: list[ObjectDescriptor]) -> list[ObjectDescriptor]:
    """
    Flatten a list of descriptors including their nested children.

    Returns all descriptors (parents and children) in a flat list.

    Args:
        descriptors: List of top-level ObjectDescriptors

    Returns:
        Flattened list including all nested children
    """
    flattened = []

    def add_descriptor(desc: ObjectDescriptor):
        """Recursively add descriptor and its children."""
        flattened.append(desc)
        for child in desc.nested_children:
            add_descriptor(child)

    for desc in descriptors:
        add_descriptor(desc)

    return flattened
