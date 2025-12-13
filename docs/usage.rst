Usage Guide
===========

This guide covers the main features and usage patterns of django-nested-seed.

Management Command
------------------

The package provides a single management command to load seed data:

.. code-block:: bash

   python manage.py nested_seed <file1.yaml> [file2.yaml ...]

You can load multiple files at once. The command will process them in order and handle all dependencies automatically.

Transaction Safety
~~~~~~~~~~~~~~~~~~

All data loading happens within a database transaction. If any error occurs during the loading process, all changes are rolled back automatically, ensuring your database remains in a consistent state.

Basic Model Creation
--------------------

The simplest way to create objects is to define them in a list under their app label and model name:

.. code-block:: yaml

   testapp:
     Category:
       - name: "Python"
         description: "Python programming language"
       - name: "Django"
         description: "Django web framework"

This creates two Category objects with the specified fields.

Reference System
----------------

Using ``$ref``
~~~~~~~~~~~~~~

You can assign reference keys to objects using the ``$ref`` field:

.. code-block:: yaml

   testapp:
     Category:
       - $ref: python
         name: "Python"
       - $ref: django
         name: "Django"

Referencing Objects
~~~~~~~~~~~~~~~~~~~

Reference objects using their key prefixed with ``$``:

.. code-block:: yaml

   testapp:
     Book:
       - title: "Django Book"
         category: "$django"  # References the category with $ref: django

Auto-generated References
~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't provide a ``$ref``, one is automatically generated:

.. code-block:: yaml

   testapp:
     Category:
       - name: "Python"  # Auto-generated ref: category_0
       - name: "Django"  # Auto-generated ref: category_1

You can reference these using ``$category_0``, ``$category_1``, etc.

ForeignKey Relationships
------------------------

Nested Objects
~~~~~~~~~~~~~~

Create related objects inline:

.. code-block:: yaml

   testapp:
     Book:
       - title: "Python Patterns"
         publisher:
           name: "Tech Books Inc"
           country: "UK"

Referenced Objects
~~~~~~~~~~~~~~~~~~

Reference previously defined objects:

.. code-block:: yaml

   testapp:
     Publisher:
       - $ref: techbooks
         name: "Tech Books Inc"
         country: "UK"

     Book:
       - title: "Python Patterns"
         publisher: "$techbooks"

Mixed Approach
~~~~~~~~~~~~~~

Combine both approaches in the same file:

.. code-block:: yaml

   testapp:
     Publisher:
       - $ref: techbooks
         name: "Tech Books Inc"
         country: "UK"

     Book:
       - title: "Python Patterns"
         publisher: "$techbooks"  # Referenced
       - title: "Django Guide"
         publisher:               # Nested
           name: "Web Publishers"
           country: "USA"

Reverse ForeignKey Relationships
---------------------------------

You can nest child collections under their parent using Django's reverse accessor:

.. code-block:: yaml

   testapp:
     Organization:
       - name: "TechCorp"
         divisions:  # Reverse FK relationship
           - name: "Engineering"
             location: "NYC"
           - name: "Sales"
             location: "LA"

The reverse accessor name follows Django's convention:

- Custom ``related_name`` if defined: use that name
- Default: ``{model_name}_set`` (e.g., ``division_set``)

OneToOne Relationships
----------------------

OneToOne fields work similarly to ForeignKey:

.. code-block:: yaml

   testapp:
     Organization:
       - name: "TechCorp"
         configuration:  # OneToOne field
           timezone: "UTC"
           currency: "USD"

ManyToMany Relationships
------------------------

Simple ManyToMany
~~~~~~~~~~~~~~~~~

Reference multiple objects using a list:

.. code-block:: yaml

   testapp:
     Technology:
       - $ref: python
         name: "Python"
       - $ref: django
         name: "Django"

     Project:
       - name: "API Rewrite"
         technologies:
           - "$python"
           - "$django"

ManyToMany with Through Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For ManyToMany relationships with extra fields on the intermediate table:

.. code-block:: yaml

   testapp:
     Project:
       - $ref: api_project
         name: "API Rewrite"

     Developer:
       - name: "Alice"
         projects:
           - project: "$api_project"
             role: "Lead"
             start_date: "2024-01-01"

Mixed ManyToMany
~~~~~~~~~~~~~~~~

Combine references and inline objects:

.. code-block:: yaml

   testapp:
     Technology:
       - $ref: python
         name: "Python"

     Project:
       - name: "API Rewrite"
         technologies:
           - "$python"        # Reference
           - name: "FastAPI"  # Inline creation

Multi-level Nesting
-------------------

You can nest relationships to any depth:

.. code-block:: yaml

   testapp:
     Organization:
       - name: "TechCorp"
         divisions:
           - name: "Engineering"
             department_set:
               - name: "Backend"
                 project_set:
                   - name: "API Rewrite"
                     task_set:
                       - title: "Design endpoints"
                         priority: "HIGH"

Loading Multiple Files
----------------------

Load multiple YAML files in a single command:

.. code-block:: bash

   python manage.py nested_seed base_data.yaml test_users.yaml products.yaml

Files are processed in the order they're specified. References from earlier files are available to later files.

Error Handling
--------------

If any error occurs during loading:

1. A descriptive error message is displayed
2. The entire transaction is rolled back
3. No partial data is committed to the database

Common errors include:

- Missing required fields
- Invalid reference keys
- Type mismatches
- Database constraint violations

Next Steps
----------

- :doc:`yaml_structure` - Complete YAML structure reference
- :doc:`database_lookups` - Learn about database lookups
- :doc:`configuration` - Configuration options
- :doc:`examples` - More comprehensive examples
