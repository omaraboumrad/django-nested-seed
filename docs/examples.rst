Examples
========

This page provides comprehensive examples demonstrating various features of django-nested-seed.

All examples can be found in the `examples/ directory <https://github.com/omaraboumrad/django-nested-seed/tree/main/examples>`_ of the GitHub repository.

Basic Examples
--------------

Simple Models
~~~~~~~~~~~~~

Creating basic objects with primitive fields.

See: `examples/01_basic_model.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/01_basic_model.yaml>`_

.. code-block:: yaml

   testapp:
     Category:
       - name: "Python"
         description: "Python programming"
       - name: "Django"
         description: "Django framework"

Relationship Examples
---------------------

ForeignKey (Nested)
~~~~~~~~~~~~~~~~~~~

Create related objects inline.

See: `examples/02_foreign_key_nested.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/02_foreign_key_nested.yaml>`_

.. code-block:: yaml

   testapp:
     Book:
       - title: "Python Patterns"
         publisher:
           name: "Tech Books Inc"
           country: "UK"

ForeignKey (Referenced)
~~~~~~~~~~~~~~~~~~~~~~~

Reference objects using ``$ref``.

See: `examples/03_foreign_key_referenced.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/03_foreign_key_referenced.yaml>`_

.. code-block:: yaml

   testapp:
     Publisher:
       - $ref: techbooks
         name: "Tech Books Inc"
         country: "UK"

     Book:
       - title: "Python Patterns"
         publisher: "$techbooks"

ForeignKey (Mixed)
~~~~~~~~~~~~~~~~~~

Combine nested and referenced approaches.

See: `examples/04_foreign_key_mixed.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/04_foreign_key_mixed.yaml>`_

.. code-block:: yaml

   testapp:
     Publisher:
       - $ref: techbooks
         name: "Tech Books Inc"

     Book:
       - title: "Book 1"
         publisher: "$techbooks"  # Referenced
       - title: "Book 2"
         publisher:               # Nested
           name: "New Publisher"

Reverse ForeignKey
~~~~~~~~~~~~~~~~~~

Nest child collections under parent.

See: `examples/05_reverse_foreign_key_nested.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/05_reverse_foreign_key_nested.yaml>`_

.. code-block:: yaml

   testapp:
     Organization:
       - name: "TechCorp"
         divisions:  # Reverse relationship
           - name: "Engineering"
             location: "NYC"
           - name: "Sales"
             location: "LA"

OneToOne Relationships
~~~~~~~~~~~~~~~~~~~~~~

Nested one-to-one fields.

See: `examples/06_one_to_one.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/06_one_to_one.yaml>`_

.. code-block:: yaml

   testapp:
     Organization:
       - name: "TechCorp"
         configuration:  # OneToOne field
           timezone: "UTC"
           currency: "USD"

ManyToMany Examples
-------------------

Basic ManyToMany
~~~~~~~~~~~~~~~~

ManyToMany with references.

See: `examples/07_many_to_many.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/07_many_to_many.yaml>`_

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

ManyToMany Through
~~~~~~~~~~~~~~~~~~

ManyToMany with custom through models.

See: `examples/08_many_to_many_through.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/08_many_to_many_through.yaml>`_

.. code-block:: yaml

   testapp:
     Project:
       - $ref: api_project
         name: "API Rewrite"

     Developer:
       - name: "Alice"
         projects:
           - project: "$api_project"
             role: "Lead Developer"
             start_date: "2024-01-01"

Mixed ManyToMany
~~~~~~~~~~~~~~~~

ManyToMany with both references and inline objects.

See: `examples/09_mixed_many_to_many.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/09_mixed_many_to_many.yaml>`_

.. code-block:: yaml

   testapp:
     Technology:
       - $ref: python
         name: "Python"

     Project:
       - name: "New Project"
         technologies:
           - "$python"        # Reference
           - name: "FastAPI"  # Inline

Advanced Examples
-----------------

Complex Multi-Level
~~~~~~~~~~~~~~~~~~~

Comprehensive example combining all features.

See: `examples/10_complex_multi_level.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/10_complex_multi_level.yaml>`_

.. code-block:: yaml

   auth:
     User:
       - $ref: alice
         username: "alice"
         email: "alice@example.com"

   testapp:
     Technology:
       - $ref: python
         name: "Python"
       - $ref: django
         name: "Django"

     Organization:
       - name: "TechCorp"
         configuration:
           timezone: "UTC"
         divisions:
           - name: "Engineering"
             department_set:
               - name: "Backend"
                 manager: "$alice"
                 project_set:
                   - name: "API Rewrite"
                     technologies:
                       - "$python"
                       - "$django"
                     task_set:
                       - title: "Design endpoints"
                         priority: "HIGH"
                         assigned_to: "$alice"

Database Lookup Examples
-------------------------

Basic Lookups
~~~~~~~~~~~~~

Reference existing database records.

See: `examples/11_database_lookups.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/11_database_lookups.yaml>`_

.. code-block:: yaml

   testapp:
     Book:
       - title: "New Book"
         author: "@username:alice"      # Lookup by field
         publisher: "@pk:1"             # Lookup by PK
         categories:
           - "@slug:python"             # Lookup in M2M
           - "@slug:django"

Mixed References and Lookups
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Combine ``$ref`` and ``@lookup``.

See: `examples/12_mixed_ref_and_lookup.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/12_mixed_ref_and_lookup.yaml>`_

.. code-block:: yaml

   auth:
     User:
       - $ref: new_user
         username: "bob"

   testapp:
     Book:
       - title: "Book 1"
         author: "@user__username:alice"  # DB lookup
       - title: "Book 2"
         author:                          # New record
           user: "$new_user"              # YAML reference
           pen_name: "Bob Writer"

YAML Feature Examples
---------------------

YAML Anchors and Aliases
~~~~~~~~~~~~~~~~~~~~~~~~~

Use YAML features for DRY (Don't Repeat Yourself).

See: `examples/13_yaml_features.yaml <https://github.com/omaraboumrad/django-nested-seed/blob/main/examples/13_yaml_features.yaml>`_

.. code-block:: yaml

   # YAML anchors and aliases
   common_config: &common_config
     timezone: "UTC"
     currency: "USD"

   testapp:
     Organization:
       - name: "Org 1"
         configuration:
           <<: *common_config
           extra_field: "value1"

       - name: "Org 2"
         configuration:
           <<: *common_config
           extra_field: "value2"

Multi-line Strings
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   testapp:
     Article:
       - title: "Long Article"
         content: |
           This is a multi-line string.
           It preserves line breaks.
           Perfect for long text content.

Real-World Scenario
-------------------

E-Commerce Seed Data
~~~~~~~~~~~~~~~~~~~~

A practical example for an e-commerce application:

.. code-block:: yaml

   auth:
     User:
       - $ref: admin
         username: "admin"
         email: "admin@shop.com"
         is_staff: true
         is_superuser: true

   shop:
     # Categories
     Category:
       - $ref: electronics
         name: "Electronics"
         slug: "electronics"
       - $ref: books
         name: "Books"
         slug: "books"

     # Products
     Product:
       - name: "Laptop"
         slug: "laptop"
         category: "$electronics"
         price: "999.99"
         stock: 50
         description: |
           High-performance laptop
           16GB RAM, 512GB SSD

       - name: "Python Book"
         slug: "python-book"
         category: "$books"
         price: "49.99"
         stock: 100

     # Customers
     Customer:
       - $ref: customer1
         user:
           username: "john"
           email: "john@example.com"
         phone: "555-0100"
         shipping_address:
           street: "123 Main St"
           city: "New York"
           country: "USA"

     # Orders
     Order:
       - customer: "$customer1"
         status: "COMPLETED"
         items:
           - product: "@slug:laptop"
             quantity: 1
             price: "999.99"
           - product: "@slug:python-book"
             quantity: 2
             price: "49.99"

Running Examples
----------------

To run any example:

.. code-block:: bash

   # Download an example
   curl -O https://raw.githubusercontent.com/omaraboumrad/django-nested-seed/main/examples/01_basic_model.yaml

   # Load it
   python manage.py nested_seed 01_basic_model.yaml

Or load multiple examples:

.. code-block:: bash

   python manage.py nested_seed examples/*.yaml

Next Steps
----------

- :doc:`usage` - Detailed usage guide
- :doc:`yaml_structure` - YAML structure reference
- :doc:`database_lookups` - Database lookups feature
