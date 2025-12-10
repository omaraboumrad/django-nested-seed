# Django Nested Seed

A Django package for loading seed data from YAML files with support for nested relationships.

## Installation

```bash
pip install django-nested-seed
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django_nested_seed',
]
```

## Quick Start

Create `data.yaml`:

```yaml
testapp:
  Author:
    - $ref: alice
      user:
        username: "alice"
        email: "alice@example.com"
      pen_name: "Alice Smith"
      bio: "Software engineer"

  Book:
    - title: "Python Patterns"
      author: "$alice"
      publisher:
        name: "Tech Books Inc"
        country: "UK"
      status: "PUBLISHED"
```

Load it:

```bash
python manage.py nested_seed data.yaml --verbose
```

## More Examples

See the [`examples/`](examples/) directory for complete examples of each feature:

- [**Basic models**](examples/01_basic_model.yaml) - Simple objects with primitive fields
- [**ForeignKey (Nested)** ](examples/02_foreign_key_nested.yaml) - Create related objects inline
- [**ForeignKey (Referenced)** ](examples/03_foreign_key_referenced.yaml) - Reference objects using `$ref_key`
- [**ForeignKey (Mixed)**](examples/04_foreign_key_mixed.yaml) - Combine nested and referenced approaches
- [**Reverse ForeignKey**](examples/05_reverse_foreign_key_nested.yaml) - Nest child collections under parent
- [**OneToOne relationships**](examples/06_one_to_one.yaml) - Nested one-to-one fields
- [**ManyToMany**](examples/07_many_to_many.yaml) - M2M with references
- [**ManyToMany (Through)**](examples/08_many_to_many_through.yaml) - M2M with custom through models
- [**Mixed ManyToMany**](examples/09_mixed_many_to_many.yaml) - M2M with both references and inline objects
- [**Complex Multi-Level**](examples/10_complex_multi_level.yaml) - Comprehensive example combining all features
- [**Database Lookups**](examples/11_database_lookups.yaml) - Reference existing database records using `@lookup`
- [**Mixed References and Lookups**](examples/12_mixed_ref_and_lookup.yaml) - Combine `$ref` and `@lookup`

## YAML Structure

```yaml
# All models use list format with Django app_label and ModelName
app_label:
  ModelName:
    # Basic object without reference
    - field_name: value
      other_field: value

    # Object with explicit reference key (for later use)
    - $ref: my_key      # Reference key for this object
      field_name: value

    # Auto-generated key (modelname_0, modelname_1, etc.)
    - field_name: value

    # ForeignKey - inline nested object
    - field_name: value
      related_field:
        nested_field: value

    # ForeignKey - reference to existing object (defined in YAML)
    - field_name: value
      related_field: "$my_key"    # Reference using $ref_key

    # ForeignKey - reference to existing database record
    - field_name: value
      related_field: "@pk:123"    # Lookup by primary key
    - field_name: value
      related_field: "@username:alice"    # Lookup by field
    - field_name: value
      related_field: "@{name:John,email:john@example.com}"    # Lookup by multiple fields

    # OneToOne - nested directly under parent
    - field_name: value
      one_to_one_field:
        nested_field: value

    # Reverse ForeignKey - nested collection
    - field_name: value
      reverse_relation_set:       # Django reverse accessor
        - child_field: value
        - child_field: value

    # ManyToMany - list of references
    - field_name: value
      many_to_many_field:
        - "$ref_key_1"            # Reference YAML object
        - "$ref_key_2"

    # ManyToMany - with database lookups
    - field_name: value
      many_to_many_field:
        - "@slug:python"          # Reference existing database record
        - "@pk:42"

    # ManyToMany - mixed references, lookups, and inline objects
    - field_name: value
      many_to_many_field:
        - "$ref_key"              # Reference YAML object
        - "@slug:existing"        # Reference database record
        - inline_field: value     # Create new object inline

    # ManyToMany with through model (extra fields)
    - field_name: value
      many_to_many_field:
        - related_object: "$ref_key"
          extra_field: value      # Through model field
          date_field: "2024-01-01"

# Reference keys must be unique across all models
```

## Features

- Zero configuration
- Supports OneToOne, ForeignKey, and ManyToMany relationships
- ManyToMany with custom through models (extra fields on intermediate table)
- Mixed relation references and inline definitions
- **Database lookups** - Reference existing database records
- Transaction safety with automatic rollback on errors
- Multiple files can be loaded together
- Topological sorting handles dependencies automatically

## Database Lookups

Reference existing database records using `@lookup` syntax instead of creating new ones:

**Lookup by primary key:**
```yaml
author: "@pk:123"  # Lookup by primary key
```

**Lookup by single field:**
```yaml
author: "@username:alice"  # Lookup by unique field
category: "@slug:python"   # Lookup by slug
```

**Lookup by multiple fields:**
```yaml
publisher: "@{name:O'Reilly Media,country:USA}"  # Lookup by multiple fields
```

**With Django's related field syntax:**
```yaml
author: "@user__username:alice"  # Lookup Author where user.username='alice'
```

**In ManyToMany fields:**
```yaml
Book:
  - title: "Django Book"
    categories:
      - "$new_category"    # Reference YAML object
      - "@slug:existing"   # Reference database record
```

**Features:**
- Results are cached to avoid redundant queries
- Clear error messages if record not found
- Works with ForeignKey, OneToOne, and ManyToMany fields
- Can be mixed with `$ref` references in the same file

## Configuration

### Custom Reference Key

Change the reference key field name in `settings.py`:

```python
NESTED_SEED_CONFIG = {
    'reference_key': 'rid',  # Use 'rid' instead of '$ref'
}
```

Then use it in your YAML:

```yaml
app:
  Category:
    - rid: python  # Using custom reference key
      name: "Python"
```

## Development

```bash
uv sync
uv run pytest
```

## Requirements

- Python 3.10+
- Django 4.2+
- PyYAML 6.0+

## License

MIT
