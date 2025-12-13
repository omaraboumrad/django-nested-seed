YAML Structure Reference
========================

This page provides a complete reference for the YAML structure used by django-nested-seed.

Basic Structure
---------------

All models use list format with Django app_label and ModelName:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         other_field: value

Basic Object
------------

Simple object without reference:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         other_field: value

Object with Reference
---------------------

Explicit reference key for later use:

.. code-block:: yaml

   app_label:
     ModelName:
       - $ref: my_key  # Reference key for this object
         field_name: value

Auto-generated Reference
------------------------

Objects without ``$ref`` get auto-generated keys:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value  # Auto: modelname_0
       - field_name: value  # Auto: modelname_1

ForeignKey - Nested
-------------------

Inline nested object:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         related_field:
           nested_field: value

ForeignKey - Referenced
-----------------------

Reference to existing object defined in YAML:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         related_field: "$my_key"  # Reference using $ref_key

ForeignKey - Database Lookup
-----------------------------

Reference existing database record:

By primary key:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         related_field: "@pk:123"

By single field:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         related_field: "@username:alice"

By multiple fields:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         related_field: "@{name:John,email:john@example.com}"

OneToOne Relationship
---------------------

Nested directly under parent:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         one_to_one_field:
           nested_field: value

Reverse ForeignKey
------------------

Nested collection using Django reverse accessor:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         reverse_relation_set:  # Django reverse accessor
           - child_field: value
           - child_field: value

ManyToMany - References
------------------------

List of references to YAML objects:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         many_to_many_field:
           - "$ref_key_1"
           - "$ref_key_2"

ManyToMany - Database Lookups
------------------------------

Reference existing database records:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         many_to_many_field:
           - "@slug:python"
           - "@pk:42"

ManyToMany - Mixed
------------------

Combine references, lookups, and inline objects:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         many_to_many_field:
           - "$ref_key"           # Reference YAML object
           - "@slug:existing"     # Reference database record
           - inline_field: value  # Create new object inline

ManyToMany - Through Model
---------------------------

With extra fields on intermediate table:

.. code-block:: yaml

   app_label:
     ModelName:
       - field_name: value
         many_to_many_field:
           - related_object: "$ref_key"
             extra_field: value      # Through model field
             date_field: "2024-01-01"

Reference Key Rules
-------------------

- Reference keys must be unique across all models
- Keys are case-sensitive
- Use descriptive names for better readability
- Auto-generated keys follow the pattern: ``{modelname}_{index}``

Field Types
-----------

CharField/TextField
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   name: "String value"
   description: "Multi-line strings work too"

IntegerField/DecimalField
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   age: 25
   price: "99.99"
   budget: "1000000.00"

BooleanField
~~~~~~~~~~~~

.. code-block:: yaml

   is_active: true
   is_published: false

DateField/DateTimeField
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   birth_date: "2000-01-01"
   created_at: "2024-01-01T10:30:00"
   published_date: "2024-12-13"

JSONField
~~~~~~~~~

.. code-block:: yaml

   metadata:
     key1: "value1"
     key2: 123
     nested:
       data: true

Choice Fields
~~~~~~~~~~~~~

.. code-block:: yaml

   status: "PUBLISHED"  # Use the choice value, not the display name

Complete Example
----------------

Here's a comprehensive example showing multiple features:

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
         version: "3.11"
       - $ref: django
         name: "Django"
         version: "4.2"

     Organization:
       - name: "TechCorp"
         code: "TC"
         founded_date: "2020-01-01"
         configuration:
           timezone: "UTC"
           currency: "USD"
         divisions:
           - name: "Engineering"
             location: "NYC"
             budget: "1000000.00"
             department_set:
               - name: "Backend"
                 code: "BE-01"
                 manager: "$alice"
                 project_set:
                   - name: "API Rewrite"
                     status: "IN_PROGRESS"
                     start_date: "2024-01-01"
                     technologies:
                       - "$python"
                       - "$django"
                     task_set:
                       - title: "Design endpoints"
                         description: "Define REST API"
                         priority: "HIGH"
                         status: "DONE"
                         assigned_to: "$alice"
                         estimated_hours: 20
