# Django Nested Seed

A Django package for loading seed data from YAML files with support for nested relationships.

You can find the fulle documentation at https://django-nested-seed.readthedocs.io/

Before you use this package you should ask yourself the following questions:

- Do I want the ability to programmatically create seed/fixture data?
- Do I want the ability to generate random seed/fixture data?
- Do I want the ability to keep my data in sync with what's in the database?
- Do I care more about using these fixtures for unit testing?

If you answered **Yes** to any of the above questions, then you're probably looking for either [Django Fixtures](<https://docs.djangoproject.com/en/5.2/topics/db/fixtures/>), [Django Management Commands](<https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/>), [Factory Boy](<https://factoryboy.readthedocs.io/en/stable/>) or any of the excellent packages available on [Django Packages' Fixture Generation Category](<https://djangopackages.org/grids/g/fixtures/>)

So when would you want to use **this** package?

- You want bootstrap data for development or demonstration purposes
- You prefer to have it declarative rather than programmatic
- You want deeply nested relationships declarations instead of flat
- Your workflow involves modifying the fixtures in the file and resetting the data, not exporting what you edited from your site.

If that's the case, then read on!

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

Given a `testapp` django application with the following models

```python
from django.db import models
from django.contrib.auth.models import User

class Person(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="people")
    pen_name = models.CharField(max_length=100)
    bio = models.TextField()

class Publisher(models.Model):
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)

class Book(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    ]

    title = models.CharField(max_length=200)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="books")
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="books")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
```

Create a `data.yaml` file with the following content:

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

then load it via the following command:

```bash
python manage.py nested_seed data.yaml
```

The command will navigate through the hierarchy and create the corresponding records according to the rules specified in the YAML Structure below.

### Another example with more features

```yaml
auth:                                   # We can target any app
  User:
    - $ref: alice                       # $ref will assign an internal reference to the node
      username: "alice"
      email: "alice@example.com"

testapp:
  Technology:
    - $ref: python
      name: "Python"
      version: "3.11"
    - $ref: django
      name: "Django"
      version: "4.2"

  Organization:
    - name: "TechCorp"
      code: "TC"
      founded_date: "2020-01-01"
      configuration:                    # O2O or FK - inline declaration
        timezone: "UTC"
        currency: "USD"
      divisions:                        # FK's Reverse relationship "divisions"
        - name: "Engineering"
          location: "NYC"
          budget: "1000000.00"
          department_set:               # FK's Reverse relationship (default `_set`)
            - name: "Backend"
              code: "BE-01"
              manager: "$alice"         # "$alice" will point to the record with $ref
              project_set:              # another reverse declaration
                - name: "API Rewrite"
                  status: "IN_PROGRESS"
                  start_date: "2024-01-01"
                  technologies:         # ManyToMany works just as well
                    - "$python"
                    - "$django"
                  task_set:             # another reverse relationship
                    - title: "Design endpoints"
                      description: "Define REST API"
                      priority: "HIGH"
                      status: "DONE"
                      assigned_to: "$alice"
                      estimated_hours: 20
                    - title: "Implement auth"
                      description: "Add JWT support"
                      priority: "HIGH"
                      status: "IN_PROGRESS"
                      assigned_to: "$alice"
                      estimated_hours: 40

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
- [**YAML Features**](examples/13_yaml_features.yaml) - YAML anchors, aliases, and multi-line strings

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
