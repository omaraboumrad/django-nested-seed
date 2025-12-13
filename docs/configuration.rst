Configuration
=============

Django-nested-seed requires minimal configuration, but offers some customization options.

Settings
--------

Add configuration to your Django settings file.

Custom Reference Key
~~~~~~~~~~~~~~~~~~~~

By default, the package uses ``$ref`` as the reference key field. You can customize this:

.. code-block:: python

   # settings.py
   NESTED_SEED_CONFIG = {
       'reference_key': 'rid',  # Use 'rid' instead of '$ref'
   }

Then use it in your YAML files:

.. code-block:: yaml

   testapp:
     Category:
       - rid: python  # Using custom reference key
         name: "Python"

     Book:
       - title: "Python Book"
         category: "rid:python"  # Reference using custom prefix

Default Configuration
~~~~~~~~~~~~~~~~~~~~~

If you don't provide any configuration, these defaults are used:

.. code-block:: python

   NESTED_SEED_CONFIG = {
       'reference_key': '$ref',
   }

Example Configuration
---------------------

Here's a complete example of custom configuration:

.. code-block:: python

   # settings.py

   INSTALLED_APPS = [
       # ... other apps
       'django_nested_seed',
   ]

   # Optional: Customize reference key
   NESTED_SEED_CONFIG = {
       'reference_key': 'id',
   }

With this configuration, your YAML would look like:

.. code-block:: yaml

   testapp:
     Category:
       - id: python
         name: "Python"

     Book:
       - title: "Python Book"
         category: "id:python"

YAML File Organization
----------------------

While not a Django setting, here are some best practices for organizing your YAML files:

Single File
~~~~~~~~~~~

For small projects, a single ``data.yaml`` file works well:

.. code-block:: text

   project/
   ├── data.yaml
   └── manage.py

Multiple Files
~~~~~~~~~~~~~~

For larger projects, split by domain or app:

.. code-block:: text

   project/
   ├── fixtures/
   │   ├── 01_users.yaml
   │   ├── 02_categories.yaml
   │   ├── 03_products.yaml
   │   └── 04_orders.yaml
   └── manage.py

Load them in order:

.. code-block:: bash

   python manage.py nested_seed fixtures/*.yaml

Environment-Specific Data
~~~~~~~~~~~~~~~~~~~~~~~~~

Organize by environment:

.. code-block:: text

   project/
   ├── fixtures/
   │   ├── base/
   │   │   ├── users.yaml
   │   │   └── categories.yaml
   │   ├── dev/
   │   │   └── test_data.yaml
   │   └── prod/
   │       └── initial_data.yaml
   └── manage.py

Load specific sets:

.. code-block:: bash

   # Development
   python manage.py nested_seed fixtures/base/*.yaml fixtures/dev/*.yaml

   # Production
   python manage.py nested_seed fixtures/base/*.yaml fixtures/prod/*.yaml

Management Command Options
--------------------------

The ``nested_seed`` command accepts the following arguments:

Basic Usage
~~~~~~~~~~~

.. code-block:: bash

   python manage.py nested_seed <file1.yaml> [file2.yaml ...]

Multiple Files
~~~~~~~~~~~~~~

.. code-block:: bash

   python manage.py nested_seed data1.yaml data2.yaml data3.yaml

Glob Patterns
~~~~~~~~~~~~~

.. code-block:: bash

   python manage.py nested_seed fixtures/*.yaml
   python manage.py nested_seed fixtures/**/*.yaml  # Recursive

Best Practices
--------------

1. **Version Control**: Keep your seed files in version control alongside your code.

2. **Naming Convention**: Use descriptive names and numbering for load order:

   - ``01_base_users.yaml``
   - ``02_categories.yaml``
   - ``03_products.yaml``

3. **Documentation**: Add comments to your YAML files to explain complex relationships:

   .. code-block:: yaml

      testapp:
        # Core categories that products reference
        Category:
          - $ref: electronics
            name: "Electronics"

4. **Separate Concerns**: Keep different types of data in separate files for maintainability.

5. **Environment Variables**: Don't hardcode sensitive data in YAML files. Use Django settings or environment variables for passwords, API keys, etc.

Transaction Behavior
--------------------

All seed data loading happens within a database transaction:

- If any error occurs, all changes are rolled back
- Database remains in consistent state
- No partial data is committed

This is built-in and cannot be disabled.

Next Steps
----------

- :doc:`usage` - Detailed usage guide
- :doc:`yaml_structure` - YAML structure reference
- :doc:`examples` - Comprehensive examples
