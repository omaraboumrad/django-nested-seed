# Documentation

This directory contains the Sphinx documentation for django-nested-seed.

## Building Documentation Locally

### Install Dependencies

Using uv:
```bash
uv pip install -r requirements.txt
```

Or using pip:
```bash
pip install -r requirements.txt
```

### Build HTML Documentation

Using uv:
```bash
cd docs
uv run sphinx-build -b html . _build/html
```

Or using make:
```bash
cd docs
make html
```

The built documentation will be in `_build/html/`. Open `_build/html/index.html` in your browser to view it.

### Clean Build Artifacts

```bash
cd docs
make clean
```

## Documentation Structure

- `index.rst` - Main documentation index
- `installation.rst` - Installation guide
- `quickstart.rst` - Quick start guide
- `usage.rst` - Detailed usage guide
- `yaml_structure.rst` - YAML structure reference
- `database_lookups.rst` - Database lookups feature
- `configuration.rst` - Configuration options
- `examples.rst` - Comprehensive examples
- `api.rst` - API reference
- `conf.py` - Sphinx configuration

## ReadTheDocs

The documentation is automatically built and published to ReadTheDocs when changes are pushed to the repository. The configuration is in `.readthedocs.yaml` at the project root.
