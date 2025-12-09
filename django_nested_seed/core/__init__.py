"""Core components for building and loading nested seed data.

This package contains the main orchestration logic and data structures:
- SeedLoader: Main orchestrator for the two-pass loading algorithm
- DescriptorBuilder: Builds ObjectDescriptor trees from parsed YAML
- ObjectRegistry: Tracks created objects and resolves references
- YAMLParser: Parses YAML files into Python data structures
- ModelResolver: Resolves model classes from app labels and model names
"""
