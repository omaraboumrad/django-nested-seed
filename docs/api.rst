API Reference
=============

This page documents the internal API of django-nested-seed. Most users won't need to interact with these classes directly, as the management command provides the primary interface.

Management Command
------------------

.. code-block:: python

   from django.core.management import call_command

   # Programmatically load seed data
   call_command('nested_seed', 'data.yaml')
   call_command('nested_seed', 'file1.yaml', 'file2.yaml')

Core Classes
------------

The package is organized into several key modules:

Parser Module
~~~~~~~~~~~~~

Located in ``django_nested_seed.parser``, this module handles YAML parsing and reference resolution.

Loader Module
~~~~~~~~~~~~~

Located in ``django_nested_seed.loader``, this module handles database operations and object creation.

Graph Module
~~~~~~~~~~~~

Located in ``django_nested_seed.graph``, this module handles topological sorting of dependencies.

Internal API
------------

.. note::
   The internal API is subject to change. For stable usage, use the management command interface.

Example Programmatic Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need to load seed data programmatically in your code:

.. code-block:: python

   from django.core.management import call_command

   def load_test_data():
       """Load test data for development environment."""
       call_command('nested_seed', 'fixtures/base.yaml')
       call_command('nested_seed', 'fixtures/test_users.yaml')

Django Integration
------------------

The package integrates with Django through:

1. **Management Command**: ``nested_seed``
2. **App Config**: ``django_nested_seed.apps.DjangoNestedSeedConfig``

Installation in Django
~~~~~~~~~~~~~~~~~~~~~~

Add to ``INSTALLED_APPS``:

.. code-block:: python

   INSTALLED_APPS = [
       # ...
       'django_nested_seed',
   ]

Settings
~~~~~~~~

Optional configuration:

.. code-block:: python

   NESTED_SEED_CONFIG = {
       'reference_key': '$ref',  # Default
   }

See :doc:`configuration` for more details.

Error Handling
--------------

The package raises standard Django and Python exceptions:

- ``ValueError`` - Invalid YAML structure or references
- ``ObjectDoesNotExist`` - Database lookup failed
- ``MultipleObjectsReturned`` - Ambiguous database lookup
- ``ValidationError`` - Django model validation failed
- ``IntegrityError`` - Database constraint violation

All operations are wrapped in a database transaction, so any error will rollback all changes.

Testing with Seed Data
----------------------

Use seed data in your tests:

.. code-block:: python

   from django.test import TransactionTestCase
   from django.core.management import call_command

   class MyTestCase(TransactionTestCase):
       def setUp(self):
           # Load seed data before each test
           call_command('nested_seed', 'fixtures/test_data.yaml')

       def test_something(self):
           # Your test code here
           pass

.. note::
   Use ``TransactionTestCase`` instead of ``TestCase`` when loading seed data in tests, as the seed loader uses database transactions.

Logging
-------

The package uses Python's standard logging module. To see debug output:

.. code-block:: python

   LOGGING = {
       'version': 1,
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
           },
       },
       'loggers': {
           'django_nested_seed': {
               'handlers': ['console'],
               'level': 'DEBUG',
           },
       },
   }

Contributing
------------

The project is open source and hosted on GitHub:

- Repository: https://github.com/omaraboumrad/django-nested-seed
- Issues: https://github.com/omaraboumrad/django-nested-seed/issues

See Also
--------

- :doc:`usage` - Detailed usage guide
- :doc:`configuration` - Configuration options
- :doc:`examples` - Comprehensive examples
