Database Lookups
================

Database lookups allow you to reference existing database records instead of creating new ones. This is useful when you want to relate new seed data to existing records.

Overview
--------

Use the ``@lookup`` syntax to reference existing database records:

.. code-block:: yaml

   testapp:
     Book:
       - title: "New Book"
         author: "@username:alice"  # Lookup existing author

Lookup Syntax
-------------

Lookup by Primary Key
~~~~~~~~~~~~~~~~~~~~~~

Reference a record by its primary key:

.. code-block:: yaml

   author: "@pk:123"

This looks up the record with ``pk=123``.

Lookup by Single Field
~~~~~~~~~~~~~~~~~~~~~~~

Reference a record by any unique field:

.. code-block:: yaml

   author: "@username:alice"
   category: "@slug:python"

This translates to:

- ``Author.objects.get(username='alice')``
- ``Category.objects.get(slug='python')``

Lookup by Multiple Fields
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use multiple fields to uniquely identify a record:

.. code-block:: yaml

   publisher: "@{name:O'Reilly Media,country:USA}"

This translates to:

.. code-block:: python

   Publisher.objects.get(name="O'Reilly Media", country="USA")

Related Field Lookups
~~~~~~~~~~~~~~~~~~~~~

Use Django's double-underscore syntax for related field lookups:

.. code-block:: yaml

   author: "@user__username:alice"

This translates to:

.. code-block:: python

   Author.objects.get(user__username='alice')

You can chain multiple levels:

.. code-block:: yaml

   task: "@project__department__name:Backend"

Usage in Different Relationship Types
--------------------------------------

ForeignKey Fields
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   testapp:
     Book:
       - title: "Django Book"
         author: "@user__username:alice"
         publisher: "@name:Tech Books Inc"

OneToOne Fields
~~~~~~~~~~~~~~~

.. code-block:: yaml

   testapp:
     Person:
       - name: "Alice"
         profile: "@user__username:alice"

ManyToMany Fields
~~~~~~~~~~~~~~~~~

Mix database lookups with YAML references:

.. code-block:: yaml

   testapp:
     Technology:
       - $ref: new_tech
         name: "FastAPI"

     Project:
       - name: "New Project"
         technologies:
           - "@slug:python"      # Existing database record
           - "@slug:django"      # Existing database record
           - "$new_tech"         # YAML reference

ManyToMany with Through Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   testapp:
     Developer:
       - name: "Bob"
         projects:
           - project: "@name:Legacy System"
             role: "Maintainer"
             start_date: "2024-01-01"

Combining with YAML References
-------------------------------

You can use both ``$ref`` references and ``@lookup`` in the same file:

.. code-block:: yaml

   auth:
     User:
       - $ref: new_user
         username: "bob"
         email: "bob@example.com"

   testapp:
     Book:
       - title: "Book by Alice"
         author: "@username:alice"      # Existing DB record
       - title: "Book by Bob"
         author:                        # YAML reference
           user: "$new_user"
           pen_name: "Bob Writer"

Features
--------

Query Caching
~~~~~~~~~~~~~

Lookup results are cached during the loading process to avoid redundant database queries. If you reference the same record multiple times, it's only queried once.

Error Handling
~~~~~~~~~~~~~~

Clear error messages are provided when:

- A record is not found
- Multiple records match the lookup criteria
- Invalid lookup syntax is used

Examples:

.. code-block:: text

   Error: No User found with lookup: username=alice
   Error: Multiple Publisher records found with lookup: country=USA

Special Characters
~~~~~~~~~~~~~~~~~~

Values containing special characters are properly escaped:

.. code-block:: yaml

   publisher: "@{name:O'Reilly Media,country:USA}"  # Single quote handled correctly

Complete Example
----------------

Here's a comprehensive example showing various lookup patterns:

.. code-block:: yaml

   auth:
     User:
       - $ref: new_user
         username: "charlie"
         email: "charlie@example.com"

   testapp:
     # Mix of new and existing categories
     Category:
       - $ref: new_category
         name: "Web Development"
         slug: "web-dev"

     # Books referencing both existing and new data
     Book:
       - title: "Python Basics"
         author: "@user__username:alice"        # Existing author
         publisher: "@pk:1"                     # Existing publisher by PK
         categories:
           - "@slug:python"                     # Existing category
           - "$new_category"                    # New category from YAML

       - title: "Django Advanced"
         author:                                # New author
           user: "$new_user"
           pen_name: "Charlie Brown"
           bio: "Web developer"
         publisher: "@{name:Tech Press,country:UK}"  # Existing by multiple fields
         categories:
           - "@slug:django"
           - "@slug:python"

Best Practices
--------------

1. **Use Primary Keys for Stability**: If you have the PK, use it. It's the most reliable lookup method.

2. **Use Unique Fields**: When looking up by field, use fields that are unique or have unique constraints.

3. **Combine with YAML References**: Use ``@lookup`` for existing data and ``$ref`` for data you're creating in the same file.

4. **Handle Missing Records**: Be prepared for lookup errors if the expected records don't exist in the database.

5. **Use Related Lookups**: Take advantage of Django's ``__`` syntax for related field lookups when needed.

Next Steps
----------

- :doc:`yaml_structure` - Complete YAML structure reference
- :doc:`examples` - More comprehensive examples
- :doc:`configuration` - Configuration options
